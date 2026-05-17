"""开盒卡片图片生成器。

字体路径通过构造时由调用方传入；
如目标字体不存在，将自动回退到 PIL 默认字体。
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


class CardMaker:
    """开盒卡片生成器。"""

    FONT_SIZE: int = 35
    TEXT_PADDING: int = 10
    BORDER_THICKNESS: int = 10
    BORDER_COLOR_RANGE: tuple[int, int] = (64, 255)
    CORNER_RADIUS: int = 30

    def __init__(
        self,
        cute_font_path: Path | None,
        emoji_font_path: Path | None,
    ) -> None:
        """构造卡片生成器。

        Args:
            cute_font_path: 中文字体路径；None 或文件不存在时使用 PIL 默认字体
            emoji_font_path: Emoji 字体路径；None 或文件不存在时使用 cute 字体替代
        """
        self.cute_font = self._load_font(cute_font_path, label="cute")
        if emoji_font_path is not None and Path(emoji_font_path).is_file():
            self.emoji_font = self._load_font(emoji_font_path, label="emoji")
        else:
            self.emoji_font = self.cute_font

    def _load_font(
        self,
        font_path: Path | None,
        *,
        label: str,
    ) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        """加载字体，失败时回退到 PIL 默认字体。"""
        if font_path is None or not Path(font_path).is_file():
            logger.warning(f"字体文件不存在，使用默认字体: {label}={font_path}")
            return ImageFont.load_default()
        try:
            return ImageFont.truetype(str(font_path), self.FONT_SIZE)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"加载字体失败 {label}={font_path}: {exc}")
            return ImageFont.load_default()

    def create(self, avatar: bytes, reply: Iterable[str]) -> bytes:
        """生成开盒卡片图片字节流。

        Args:
            avatar: 头像 PNG/JPEG 字节流
            reply: 信息行列表

        Returns:
            生成的 PNG 字节流
        """
        reply_str = "\n".join(list(reply))

        # 估算文本尺寸（emoji 字符用占位符“一”代替宽度）
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        no_emoji_reply = "".join("一" if emoji.is_emoji(c) else c for c in reply_str)
        bbox = temp_draw.textbbox((0, 0), no_emoji_reply, font=self.cute_font)
        text_width = int(bbox[2] - bbox[0])
        text_height = int(bbox[3] - bbox[1])

        img_height = text_height + self.TEXT_PADDING * 2

        try:
            avatar_img = Image.open(BytesIO(avatar)).convert("RGBA")
            avatar_size = text_height
            avatar_img = avatar_img.resize((avatar_size, avatar_size))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"处理头像失败，使用空白头像替代: {exc}")
            avatar_size = text_height
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

    def _draw_multi(
        self,
        img: Image.Image,
        text: str,
        text_x: int = 10,
        text_y: int = 10,
    ) -> None:
        """逐字符绘制多行文本，支持 emoji 字体回退。"""
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
                if char in emoji.EMOJI_DATA and self.emoji_font is not self.cute_font:
                    draw.text(
                        (current_x, current_y + 10),
                        char,
                        font=self.emoji_font,
                        fill=line_color,
                    )
                    bbox = self.emoji_font.getbbox(char)
                else:
                    draw.text(
                        (current_x, current_y),
                        char,
                        font=self.cute_font,
                        fill=line_color,
                    )
                    bbox = self.cute_font.getbbox(char)

                current_x += bbox[2] - bbox[0]

            current_y += 40
