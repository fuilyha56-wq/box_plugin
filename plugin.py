"""Box Plugin 入口。

基于 OneBot 协议获取 QQ 用户信息，并以图片卡片形式展示。
"""

from __future__ import annotations

from pathlib import Path

from src.app.plugin_system.api.log_api import get_logger
from src.app.plugin_system.base import BasePlugin, register_plugin

from .commands.box_command import BoxCommand
from .config import BoxPluginConfig
from .core.box_core import BoxCore
from .handlers.group_member_handler import GroupMemberHandler

logger = get_logger("box_plugin")


@register_plugin
class BoxPlugin(BasePlugin):
    """开盒插件主类。"""

    plugin_name: str = "box_plugin"
    plugin_description: str = "基于 OneBot 协议获取 QQ 用户信息，并以图片卡片形式展示"
    plugin_version: str = "2.0.0"

    configs: list[type] = [BoxPluginConfig]
    dependent_components: list[str] = []

    box_core: BoxCore | None

    def __init__(self, config: BoxPluginConfig | None = None) -> None:
        """初始化插件。

        Args:
            config: 插件配置实例
        """
        super().__init__(config)
        self.box_core = None
        # 插件根目录（plugin.py 所在目录）
        self.plugin_dir: Path = Path(__file__).resolve().parent

    async def on_plugin_loaded(self) -> None:
        """插件加载完成后的钩子。"""
        if isinstance(self.config, BoxPluginConfig) and not self.config.plugin.enabled:
            logger.info("box_plugin 已在配置中禁用")
            return

        try:
            self.box_core = BoxCore(plugin_dir=self.plugin_dir, plugin=self)
            await self.box_core.prepare_resources()
            logger.info("box_plugin 已加载，box_core 初始化完成")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"box_plugin 加载失败: {exc}", exc_info=True)
            self.box_core = None

    async def on_plugin_unloaded(self) -> None:
        """插件卸载时的钩子。"""
        if self.box_core is not None:
            await self.box_core.cleanup()
            self.box_core = None

    def get_components(self) -> list[type]:
        """返回插件提供的组件列表。"""
        if isinstance(self.config, BoxPluginConfig) and not self.config.plugin.enabled:
            return []
        return [BoxCommand, GroupMemberHandler]
