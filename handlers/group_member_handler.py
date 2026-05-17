"""Box Plugin 群成员事件处理器。

订阅 ON_NOTICE_RECEIVED 事件，识别群成员入群/退群通知，
按配置自动开盒并在群聊推送结果图片。
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

from src.app.plugin_system.api.log_api import get_logger
from src.app.plugin_system.api.send_api import send_image, send_text
from src.app.plugin_system.api.stream_api import get_stream_info
from src.app.plugin_system.base import BaseEventHandler
from src.app.plugin_system.types import EventType
from src.kernel.event import EventDecision

from ..config import BoxPluginConfig

if TYPE_CHECKING:
    from ..plugin import BoxPlugin

logger = get_logger("box_plugin.handler")


# 入群/退群类型识别
_JOIN_NOTICE_TYPES = {"group_increase", "group_member_increase", "join"}
_LEAVE_NOTICE_TYPES = {"group_decrease", "group_member_decrease", "leave", "kick"}


class GroupMemberHandler(BaseEventHandler):
    """群成员入群/退群事件自动开盒处理器。"""

    handler_name: str = "box_group_member_handler"
    handler_description: str = "群成员入群/退群事件自动开盒"
    weight: int = 10
    intercept_message: bool = False
    init_subscribe: list[EventType | str] = [EventType.ON_NOTICE_RECEIVED]

    plugin: "BoxPlugin"

    # ------------------------------------------------------------------ #
    # 主入口
    # ------------------------------------------------------------------ #

    async def execute(
        self,
        event_name: str,
        params: dict[str, Any],
    ) -> tuple[EventDecision, dict[str, Any]]:
        """处理通知事件。"""
        try:
            await self._handle(params)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"自动开盒处理失败: {exc}")
        return EventDecision.SUCCESS, params

    # ------------------------------------------------------------------ #
    # 业务实现
    # ------------------------------------------------------------------ #

    def _config(self) -> BoxPluginConfig:
        """读取插件配置。"""
        config = getattr(self.plugin, "config", None)
        if isinstance(config, BoxPluginConfig):
            return config
        return BoxPluginConfig()

    async def _handle(self, params: dict[str, Any]) -> None:
        """识别通知类型并执行自动开盒。"""
        notice_type = str(
            params.get("notice_type")
            or params.get("event_type")
            or params.get("type")
            or ""
        ).lower()
        if notice_type not in _JOIN_NOTICE_TYPES and notice_type not in _LEAVE_NOTICE_TYPES:
            return

        user_id = str(params.get("user_id") or "")
        group_id = str(params.get("group_id") or "")
        if not user_id or not group_id:
            return

        config = self._config()

        # 自动开盒群白名单
        whitelist = [str(g) for g in config.groups.auto_box_groups]
        if whitelist and group_id not in whitelist:
            return

        # 保护名单
        protect_ids = {str(pid) for pid in config.protection.protect_ids}
        if user_id in protect_ids:
            return

        plugin = self.plugin
        if plugin.box_core is None:
            logger.warning("自动开盒触发但 box_core 尚未初始化")
            return

        try:
            image_data = await plugin.box_core.box_user(
                target_id=user_id,
                group_id=group_id,
                sender_id=user_id,
                is_admin=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"自动开盒 {user_id} 失败: {exc}")
            return

        if not image_data:
            return

        # 通过 stream_id 推送到当前群
        stream_id = str(params.get("stream_id") or "")
        if not stream_id:
            # 尝试通过 group_id + platform 反向解析
            platform = str(params.get("platform") or "")
            if not platform:
                logger.debug("自动开盒：无法确定目标 stream_id")
                return
            from src.app.plugin_system.types import ChatStream

            try:
                stream_id = ChatStream.generate_stream_id(platform, group_id=group_id)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"生成 stream_id 失败: {exc}")
                return

        info = await get_stream_info(stream_id)
        if not isinstance(info, dict):
            return

        action_label = "新成员入群" if notice_type in _JOIN_NOTICE_TYPES else "成员退群"
        await send_text(
            f"[{action_label}] 自动开盒 {user_id}",
            stream_id=stream_id,
        )
        await send_image(
            image_data=base64.b64encode(image_data).decode("utf-8"),
            stream_id=stream_id,
        )
