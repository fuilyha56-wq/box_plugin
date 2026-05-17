"""Box Plugin 核心业务逻辑。"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.app.plugin_system.api import adapter_api
from src.app.plugin_system.api.log_api import get_logger

from ..config import (
    DEFAULT_CJK_KR_FONT_URL,
    DEFAULT_CUTE_FONT_URL,
    DEFAULT_EMOJI_FONT_URL,
    DEFAULT_LATIN_FONT_URL,
    BoxPluginConfig,
)
from .draw import CardMaker
from .field_mapping import (
    ALL_LABELS,
    FIELD_MAPPING,
    LABEL_TO_CONFIG_KEY,
    LABEL_TO_KEY,
    get_constellation,
    get_zodiac,
)
from .utils import download_file, get_avatar, render_digest


# 已知失效的历史 URL 片段，命中即视为旧默认值，自动改用最新默认 URL
_DEPRECATED_CUTE_FONT_FRAGMENTS: tuple[str, ...] = (
    "astrbot_plugin_box@master/font/",
)
_DEPRECATED_EMOJI_FONT_FRAGMENTS: tuple[str, ...] = ()

if TYPE_CHECKING:
    from ..plugin import BoxPlugin

logger = get_logger("box_plugin.core")


# 字体文件名（保存到 plugin_dir/data/fonts/ 下）
_CUTE_FONT_FILENAME = "cute_font.ttf"
_EMOJI_FONT_FILENAME = "NotoColorEmoji.ttf"
_LATIN_FONT_FILENAME = "NotoSans-Regular.ttf"
_CJK_KR_FONT_FILENAME = "NotoSansKR-Regular.otf"


class BoxCore:
    """开盒核心：负责字体准备、用户信息获取与卡片渲染。"""

    def __init__(self, *, plugin_dir: Path, plugin: "BoxPlugin") -> None:
        """初始化核心。

        Args:
            plugin_dir: 插件目录
            plugin: 插件实例（用于读取配置）
        """
        self.plugin = plugin
        self.plugin_dir = Path(plugin_dir)
        self.data_dir = self.plugin_dir / "data"
        self.cache_dir = self.data_dir / "cache"
        self.font_dir = self.data_dir / "fonts"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.font_dir.mkdir(parents=True, exist_ok=True)
        self.renderer: CardMaker | None = None

    # ------------------------------------------------------------------ #
    # 配置与资源
    # ------------------------------------------------------------------ #

    def _config(self) -> BoxPluginConfig:
        """读取插件配置，失败时回退到默认配置。"""
        config = getattr(self.plugin, "config", None)
        if isinstance(config, BoxPluginConfig):
            return config
        return BoxPluginConfig()

    @staticmethod
    def _resolve_font_url(
        configured_url: str,
        default_url: str,
        deprecated_fragments: tuple[str, ...],
    ) -> str:
        """若配置中的 URL 命中已知失效片段，则自动回退到最新默认 URL。"""
        if not configured_url:
            return default_url
        for fragment in deprecated_fragments:
            if fragment in configured_url:
                logger.warning(
                    "检测到失效的历史字体 URL，已自动改用最新默认地址: "
                    f"{configured_url} -> {default_url}"
                )
                return default_url
        return configured_url

    async def _download_font(
        self,
        primary_url: str,
        fallback_url: str,
        target_path: Path,
        timeout: float,
    ) -> bool:
        """下载字体文件；主 URL 失败时自动回退到默认 URL。"""
        if primary_url and await download_file(primary_url, target_path, timeout=timeout):
            return True
        if fallback_url and fallback_url != primary_url:
            logger.info(f"主 URL 下载失败，回退到默认地址: {fallback_url}")
            return await download_file(fallback_url, target_path, timeout=timeout)
        return False

    async def prepare_resources(self) -> None:
        """确保字体资源就绪，并构建卡片渲染器。"""
        config = self._config()
        cute_font_path = self.font_dir / _CUTE_FONT_FILENAME
        emoji_font_path = self.font_dir / _EMOJI_FONT_FILENAME
        latin_font_path = self.font_dir / _LATIN_FONT_FILENAME
        cjk_kr_font_path = self.font_dir / _CJK_KR_FONT_FILENAME

        # 下载可爱字体
        if not cute_font_path.is_file() and config.font.cute_font_url:
            logger.info("中文字体不存在，尝试下载…")
            cute_url = self._resolve_font_url(
                config.font.cute_font_url,
                DEFAULT_CUTE_FONT_URL,
                _DEPRECATED_CUTE_FONT_FRAGMENTS,
            )
            await self._download_font(
                cute_url,
                DEFAULT_CUTE_FONT_URL,
                cute_font_path,
                config.font.download_timeout,
            )

        # 下载 emoji 字体
        emoji_target: Path | None = emoji_font_path
        if config.font.skip_emoji_font:
            emoji_target = None
        elif not emoji_font_path.is_file() and config.font.emoji_font_url:
            logger.info("Emoji 字体不存在，尝试下载…")
            emoji_url = self._resolve_font_url(
                config.font.emoji_font_url,
                DEFAULT_EMOJI_FONT_URL,
                _DEPRECATED_EMOJI_FONT_FRAGMENTS,
            )
            ok = await self._download_font(
                emoji_url,
                DEFAULT_EMOJI_FONT_URL,
                emoji_font_path,
                config.font.download_timeout,
            )
            if not ok:
                emoji_target = None

        # 下载 Latin fallback 字体（俄/希腊/拉丁扩展）
        if not latin_font_path.is_file() and config.font.latin_font_url:
            logger.info("Latin fallback 字体不存在，尝试下载…")
            await self._download_font(
                config.font.latin_font_url,
                DEFAULT_LATIN_FONT_URL,
                latin_font_path,
                config.font.download_timeout,
            )

        # 下载韩语/日语假名 fallback 字体
        if not cjk_kr_font_path.is_file() and config.font.cjk_kr_font_url:
            logger.info("韩语/日语 fallback 字体不存在，尝试下载…")
            await self._download_font(
                config.font.cjk_kr_font_url,
                DEFAULT_CJK_KR_FONT_URL,
                cjk_kr_font_path,
                config.font.download_timeout,
            )

        self.renderer = CardMaker(
            cute_font_path=cute_font_path if cute_font_path.is_file() else None,
            emoji_font_path=emoji_target if (emoji_target and emoji_target.is_file()) else None,
            latin_font_path=latin_font_path if latin_font_path.is_file() else None,
            cjk_kr_font_path=cjk_kr_font_path if cjk_kr_font_path.is_file() else None,
        )

    # ------------------------------------------------------------------ #
    # 用户信息获取
    # ------------------------------------------------------------------ #

    async def _send_adapter_command(
        self,
        command_name: str,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        """通过 adapter_api 调用底层适配器命令。"""
        config = self._config()
        signature = config.adapter.adapter_signature
        timeout = config.adapter.api_timeout
        try:
            response = await adapter_api.send_adapter_command(
                adapter_sign=signature,
                command_name=command_name,
                command_data=params,
                timeout=timeout,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"调用适配器命令失败 {command_name}: {exc}")
            return None

        if not isinstance(response, dict):
            return None
        if response.get("status") not in (None, "ok", "success"):
            logger.debug(f"适配器返回非成功状态: {response}")
        data = response.get("data")
        return data if isinstance(data, dict) else None

    async def _get_user_info(
        self,
        user_id: str,
        group_id: str,
    ) -> dict[str, Any] | None:
        """获取陌生人信息和群成员信息。"""
        try:
            stranger_info = await self._send_adapter_command(
                "get_stranger_info",
                {"user_id": int(user_id)},
            ) or {}
        except ValueError:
            logger.warning(f"无效的 user_id: {user_id}")
            return None

        member_info: dict[str, Any] = {}
        if group_id:
            try:
                member_info = await self._send_adapter_command(
                    "get_group_member_info",
                    {"group_id": int(group_id), "user_id": int(user_id), "no_cache": True},
                ) or {}
            except ValueError:
                logger.warning(f"无效的 group_id: {group_id}")

        return {"stranger_info": stranger_info, "member_info": member_info}

    # ------------------------------------------------------------------ #
    # 渲染与缓存
    # ------------------------------------------------------------------ #

    def _enabled_keys(self, config: BoxPluginConfig) -> set[str]:
        """根据配置中的 display section，得到启用的字段 key 集合。"""
        display = config.display
        enabled: set[str] = set()
        for label in ALL_LABELS:
            config_key = LABEL_TO_CONFIG_KEY.get(label)
            if config_key is None:
                continue
            if getattr(display, config_key, True):
                enabled.add(LABEL_TO_KEY[label])
        return enabled

    def _transform_user_info(
        self,
        user_info: dict[str, Any],
        config: BoxPluginConfig,
    ) -> list[str]:
        """根据字段映射表与启用字段生成显示行。"""
        stranger_info = user_info.get("stranger_info") or {}
        member_info = user_info.get("member_info") or {}
        enabled_keys = self._enabled_keys(config)

        reply: list[str] = []

        for field in FIELD_MAPPING:
            key = field["key"]
            label = field["label"]
            source = field.get("source", "info1")

            if key not in enabled_keys:
                continue

            if source == "computed":
                computed_lines = self._compute_field(
                    key, label, stranger_info, member_info
                )
                reply.extend(computed_lines)
                continue

            data = stranger_info if source == "info1" else member_info
            value = data.get(key)

            if not value:
                continue
            if value in field.get("skip_values", []):
                continue

            transform = field.get("transform")
            if transform:
                try:
                    value = transform(value)
                except Exception:  # noqa: BLE001
                    value = None
                if not value:
                    continue

            suffix = field.get("suffix", "")

            if field.get("multiline"):
                import textwrap

                wrap_width = field.get("wrap_width", 15)
                lines = textwrap.wrap(text=f"{label}：{value}", width=wrap_width)
                reply.extend(lines)
            else:
                reply.append(f"{label}：{value}{suffix}")

        return reply

    def _compute_field(
        self,
        key: str,
        label: str,
        info1: dict[str, Any],
        info2: dict[str, Any],
    ) -> list[str]:
        """处理需要计算的字段（生日/星座/生肖/家乡现居）。"""
        if key == "birthday":
            year = info1.get("birthday_year")
            month = info1.get("birthday_month")
            day = info1.get("birthday_day")
            if year and month and day:
                return [f"{label}：{year}-{month}-{day}"]
            return []

        if key == "constellation":
            month = info1.get("birthday_month")
            day = info1.get("birthday_day")
            if month and day:
                return [f"{label}：{get_constellation(int(month), int(day))}"]
            return []

        if key == "zodiac":
            year = info1.get("birthday_year")
            month = info1.get("birthday_month")
            day = info1.get("birthday_day")
            if year and month and day:
                return [f"{label}：{get_zodiac(int(year), int(month), int(day))}"]
            return []

        if key == "address":
            country = info1.get("country")
            province = info1.get("province")
            city = info1.get("city")
            if country == "中国" and (province or city):
                return [f"{label}：{province or ''}-{city or ''}"]
            if country:
                return [f"{label}：{country}"]
            return []

        if key == "detail_address":
            address = info1.get("address")
            if address and address != "-":
                return [f"{label}：{address}"]
            return []

        return []

    async def box_user(
        self,
        target_id: str,
        group_id: str,
        sender_id: str,
        *,
        is_admin: bool = False,
    ) -> bytes | None:
        """执行一次开盒操作。

        Args:
            target_id: 被开盒用户 ID
            group_id: 群聊 ID，私聊时传空串
            sender_id: 触发用户 ID
            is_admin: 是否为 Bot 管理员

        Returns:
            生成的图片字节流，失败时返回 None
        """
        config = self._config()

        if config.basic.only_admin and not is_admin and target_id != sender_id:
            logger.info("非管理员尝试开盒他人，已被阻止")
            return None

        protect_ids = [str(pid) for pid in config.protection.protect_ids]
        if target_id in protect_ids and target_id != sender_id:
            logger.info(f"用户 {target_id} 在保护名单中，无法开盒")
            return None

        user_info = await self._get_user_info(target_id, group_id)
        if not user_info or not user_info.get("stranger_info"):
            logger.warning(f"无法获取用户 {target_id} 的信息")
            return None

        avatar = await get_avatar(target_id) or self._fallback_avatar()
        display = self._transform_user_info(user_info, config)
        if not display:
            display = [f"QQ号：{target_id}", "（暂无可显示字段）"]

        digest = render_digest(display, avatar)
        cache_path = self.cache_dir / f"{target_id}_{group_id or 'private'}_{digest}.png"
        if cache_path.is_file():
            logger.debug(f"命中缓存: {cache_path}")
            return cache_path.read_bytes()

        if self.renderer is None:
            await self.prepare_resources()
        assert self.renderer is not None
        image = self.renderer.create(avatar, display)
        try:
            cache_path.write_bytes(image)
        except OSError as exc:
            logger.warning(f"写入缓存失败: {exc}")
        return image

    def _fallback_avatar(self) -> bytes:
        """生成默认空白头像。"""
        from io import BytesIO

        from PIL import Image

        img = Image.new("RGB", (640, 640), (255, 255, 255))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # ------------------------------------------------------------------ #
    # 清理
    # ------------------------------------------------------------------ #

    async def cleanup(self) -> None:
        """卸载时清理资源。"""
        config = self._config()
        if config.basic.clean_cache and self.cache_dir.exists():
            try:
                shutil.rmtree(self.cache_dir)
                logger.debug(f"已清空缓存: {self.cache_dir}")
            except OSError as exc:
                logger.warning(f"清空缓存失败: {exc}")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
