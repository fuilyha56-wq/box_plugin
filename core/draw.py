"""开盒卡片图片生成器。

字体路径通过构造时由调用方传入；
如目标字体不存在，将自动回退到 PIL 默认字体。

NotoColorEmoji.ttf 是 CBDT 位图字体，PIL 加载时必须使用其 strike 尺寸（109），
绘制时启用 ``embedded_color=True``，再缩放到目标行高。

多字体路由：cute → latin → cjk_kr，按字符所属 Unicode 区段+字体 cmap 决定使用哪个字体。
"""

from __future__ import annotations

import io
import random
from io import BytesIO
from pathlib import Path
from typing import Iterable

import emoji
from PIL import Image, ImageDraw, ImageFont

from src.app.plugin_system.api.log_api import get_logger

logger = get_logger("box_plugin.draw")


# NotoColorEmoji 唯一可用的位图 strike 尺寸
_EMOJI_NATIVE_SIZE: int = 109


def _read_cmap(font_path: Path) -> set[int]:
    """读取字体的 cmap，返回所有受支持的码点集合；失败时返回空集。"""
    try:
        from fontTools.ttLib import TTFont  # type: ignore
    except ImportError:
        logger.warning("fontTools 未安装，无法做精确字符路由（仅按区段近似）")
        return set()
    try:
        font = TTFont(str(font_path), lazy=True)
        cmap = font.getBestCmap() or {}
        return set(cmap.keys())
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"读取 cmap 失败 {font_path}: {exc}")
        return set()


class CardMaker:
    """开盒卡片生成器。"""

    FONT_SIZE: int = 35
    TEXT_PADDING: int = 10
    BORDER_THICKNESS: int = 10
    BORDER_COLOR_RANGE: tuple[int, int] = (64, 255)
    CORNER_RADIUS: int = 30
    LINE_HEIGHT: int = 40

    def __init__(
        self,
        cute_font_path: Path | None,
        emoji_font_path: Path | None,
        latin_font_path: Path | None = None,
        cjk_kr_font_path: Path | None = None,
    ) -> None:
        """构造卡片生成器。

        Args:
            cute_font_path: 主中文字体路径（可爱字体）；缺失时使用 PIL 默认字体
            emoji_font_path: Emoji 字体路径（NotoColorEmoji，CBDT 位图字体）
            latin_font_path: 拉丁/俄语/希腊语 fallback 字体（NotoSans）
            cjk_kr_font_path: 韩语/日语假名 fallback 字体（NotoSansKR）
        """
        self.cute_font = self._load_truetype(cute_font_path, self.FONT_SIZE, label="cute")
        self.cute_cps: set[int] = (
            _read_cmap(cute_font_path) if cute_font_path and Path(cute_font_path).is_file() else set()
        )

        self.latin_font: ImageFont.FreeTypeFont | None = None
        self.latin_cps: set[int] = set()
        if latin_font_path and Path(latin_font_path).is_file():
            font = self._try_load_truetype(latin_font_path, self.FONT_SIZE)
            if font is not None:
                self.latin_font = font
                self.latin_cps = _read_cmap(latin_font_path)

        self.cjk_kr_font: ImageFont.FreeTypeFont | None = None
        self.cjk_kr_cps: set[int] = set()
        if cjk_kr_font_path and Path(cjk_kr_font_path).is_file():
            font = self._try_load_truetype(cjk_kr_font_path, self.FONT_SIZE)
            if font is not None:
                self.cjk_kr_font = font
                self.cjk_kr_cps = _read_cmap(cjk_kr_font_path)

        self.emoji_font: ImageFont.FreeTypeFont | None = self._load_emoji_font(emoji_font_path)

    # ------------------------------------------------------------------ #
    # 字体加载
    # ------------------------------------------------------------------ #

    @staticmethod
    def _try_load_truetype(
        font_path: Path, size: int
    ) -> ImageFont.FreeTypeFont | None:
        """尝试加载字体，失败返回 None。"""
        try:
            return ImageFont.truetype(str(font_path), size)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"加载字体失败 {font_path}: {exc}")
            return None

    @staticmethod
    def _load_truetype(
        font_path: Path | None,
        size: int,
        *,
        label: str,
    ) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        """加载普通 TrueType 字体，失败时回退到 PIL 默认字体。"""
        if font_path is None or not Path(font_path).is_file():
            logger.warning(f"字体文件不存在，使用默认字体: {label}={font_path}")
            return ImageFont.load_default()
        try:
            return ImageFont.truetype(str(font_path), size)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"加载字体失败 {label}={font_path}: {exc}")
            return ImageFont.load_default()

    @staticmethod
    def _load_emoji_font(font_path: Path | None) -> ImageFont.FreeTypeFont | None:
        """加载彩色 emoji 字体。

        NotoColorEmoji 必须使用其 strike 尺寸 109，
        否则 PIL 会抛 ``invalid pixel size``。
        """
        if font_path is None or not Path(font_path).is_file():
            return None
        try:
            return ImageFont.truetype(str(font_path), _EMOJI_NATIVE_SIZE)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"加载 emoji 字体失败 {font_path}: {exc}")
            return None

    # ------------------------------------------------------------------ #
    # 字体路由
    # ------------------------------------------------------------------ #

    def _pick_font(self, char: str) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        """按 cmap 优先级选字体：cute → cjk_kr → latin → cute(默认)。

        Args:
            char: 单个字符

        Returns:
            最适合渲染该字符的字体对象
        """
        if not char:
            return self.cute_font
        cp = ord(char[0])

        # 1) 主字体（cute）含该字符
        if cp in self.cute_cps:
            return self.cute_font

        # 2) 韩语 / 日语假名 / 韩文兼容 → cjk_kr 优先
        is_korean_or_kana = (
            0xAC00 <= cp <= 0xD7AF  # Hangul Syllables
            or 0x3040 <= cp <= 0x30FF  # Hiragana + Katakana
            or 0x3130 <= cp <= 0x318F  # Hangul Compat Jamo
            or 0x1100 <= cp <= 0x11FF  # Hangul Jamo
        )
        if is_korean_or_kana and self.cjk_kr_font is not None and cp in self.cjk_kr_cps:
            return self.cjk_kr_font

        # 3) latin（俄/希腊/拉丁扩展等）
        if self.latin_font is not None and cp in self.latin_cps:
            return self.latin_font

        # 4) 仍兜底 cjk_kr（韩文/CJK 扩展等）
        if self.cjk_kr_font is not None and cp in self.cjk_kr_cps:
            return self.cjk_kr_font

        # 5) 兜底回到 cute（即便没 glyph，也至少得到 .notdef）
        return self.cute_font

    # ------------------------------------------------------------------ #
    # 入口
    # ------------------------------------------------------------------ #

    def create(self, avatar: bytes, reply: Iterable[str]) -> bytes:
        """生成开盒卡片图片字节流。

        Args:
            avatar: 头像 PNG/JPEG 字节流
            reply: 信息行列表

        Returns:
            生成的 PNG 字节流
        """
        lines = list(reply)
        reply_str = "\n".join(lines)

        # 估算文本尺寸（emoji 字符按 FONT_SIZE 方块占位，避免被低估）
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        no_emoji_reply = "".join(
            "一" if self._is_emoji(c) else c for c in reply_str
        )
        bbox = temp_draw.textbbox((0, 0), no_emoji_reply, font=self.cute_font)
        text_width = int(bbox[2] - bbox[0])
        text_height = int(bbox[3] - bbox[1])

        # 行高使用稳定值，避免不同字体导致差异
        line_count = max(len(lines), 1)
        text_block_height = max(text_height, self.LINE_HEIGHT * line_count)

        img_height = text_block_height + self.TEXT_PADDING * 2

        try:
            avatar_img = Image.open(BytesIO(avatar)).convert("RGBA")
            avatar_size = text_block_height
            avatar_img = avatar_img.resize((avatar_size, avatar_size))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"处理头像失败，使用空白头像替代: {exc}")
            avatar_size = text_block_height
            avatar_img = Image.new("RGBA", (avatar_size, avatar_size), (255, 255, 255, 255))

        img_width = avatar_img.width + text_width + self.TEXT_PADDING * 2

        img = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 255))

        # 圆角头像
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [(0, 0), (avatar_size, avatar_size)],
            self.CORNER_RADIUS,
            fill=255,
        )
        avatar_img.putalpha(mask)
        img.paste(avatar_img, (0, (img_height - avatar_size) // 2), mask)

        # 文本
        self._draw_multi(
            img,
            reply_str,
            avatar_img.width + self.TEXT_PADDING,
            self.TEXT_PADDING,
        )

        # 随机彩色边框
        border_color = tuple(
            random.randint(*self.BORDER_COLOR_RANGE) for _ in range(3)
        )
        border_img = Image.new(
            "RGBA",
            (
                img_width + self.BORDER_THICKNESS * 2,
                img_height + self.BORDER_THICKNESS * 2,
            ),
            border_color,
        )
        border_img.paste(img, (self.BORDER_THICKNESS, self.BORDER_THICKNESS))

        out = io.BytesIO()
        border_img.save(out, format="PNG")
        return out.getvalue()

    # ------------------------------------------------------------------ #
    # 文本绘制
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_emoji(char: str) -> bool:
        """判断字符是否为 emoji（含 EMOJI_DATA 主表的所有码点）。"""
        try:
            if char in emoji.EMOJI_DATA:
                return True
        except Exception:  # noqa: BLE001
            pass
        return emoji.is_emoji(char)

    def _draw_multi(
        self,
        img: Image.Image,
        text: str,
        text_x: int = 10,
        text_y: int = 10,
    ) -> None:
        """逐字符绘制多行文本，支持 emoji 字体回退与多字体路由。"""
        lines = text.split("\n")
        draw = ImageDraw.Draw(img)
        current_y = text_y

        for line in lines:
            line_color = (
                random.randint(0, 128),
                random.randint(0, 128),
                random.randint(0, 128),
                random.randint(240, 255),
            )
            current_x = text_x

            for char in line:
                if self._is_emoji(char) and self.emoji_font is not None:
                    advance = self._draw_emoji_char(
                        img, char, current_x, current_y
                    )
                    current_x += advance
                else:
                    font = self._pick_font(char)
                    draw.text(
                        (current_x, current_y),
                        char,
                        font=font,
                        fill=line_color,
                    )
                    bbox = font.getbbox(char)
                    current_x += bbox[2] - bbox[0]

            current_y += self.LINE_HEIGHT

    def _draw_emoji_char(
        self,
        img: Image.Image,
        char: str,
        x: int,
        y: int,
    ) -> int:
        """在独立画布上以原生尺寸渲染 emoji，再缩放贴回主图。

        Returns:
            该字符占用的水平宽度（像素）
        """
        assert self.emoji_font is not None

        target_size = self.FONT_SIZE
        # 原生位图渲染 (109x109)，用 RGBA 透明背景
        emoji_img = Image.new(
            "RGBA",
            (_EMOJI_NATIVE_SIZE + 8, _EMOJI_NATIVE_SIZE + 8),
            (255, 255, 255, 0),
        )
        emoji_draw = ImageDraw.Draw(emoji_img)
        try:
            emoji_draw.text(
                (0, 0),
                char,
                font=self.emoji_font,
                embedded_color=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"绘制 emoji 失败 {char!r}: {exc}")
            return target_size

        # 裁掉透明边再缩放，避免 advance 过大
        bbox = emoji_img.getbbox()
        if bbox is None:
            return target_size
        cropped = emoji_img.crop(bbox)
        scale = target_size / cropped.height if cropped.height else 1.0
        new_w = max(1, int(cropped.width * scale))
        new_h = max(1, int(cropped.height * scale))
        scaled = cropped.resize((new_w, new_h), Image.LANCZOS)

        img.paste(scaled, (x, y), scaled)
        return new_w
