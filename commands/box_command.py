"""Box Plugin 开盒命令。

支持触发词：/盒 与 /开盒。
- 在群聊：必须 @用户 或提供 QQ 号，否则只能开盒自己
- 在私聊：默认开盒自己

底层通过 adapter_api 调用 OneBot 协议适配器获取用户信息。
"""

from __future__ import annotations

import asyncio
import base64
import re
from typing import TYPE_CHECKING

from src.app.plugin_system.api import permission_api
from src.app.plugin_system.api.adapter_api import send_adapter_command
from src.app.plugin_system.api.log_api import get_logger
from src.app.plugin_system.api.send_api import send_image
from src.app.plugin_system.api.stream_api import get_stream_info
from src.app.plugin_system.base import BaseCommand, cmd_route
from src.app.plugin_system.types import ChatType, PermissionLevel

from ..config import BoxPluginConfig

if TYPE_CHECKING:
    from ..plugin import BoxPlugin

logger = get_logger("box_plugin.command")

# 匹配 @<昵称:QQ号> 格式
_AT_PATTERN = re.compile(r"^@<([^>:]*):([^>]+)>$")
# 纯 QQ 号
_QQ_PATTERN = re.compile(r"^\d{5,11}$")


class BoxCommand(BaseCommand):
    """开盒命令组件。

    路由结构：
      /盒                — 在私聊开盒自己；群聊提示需要 @
      /盒 <QQ号|@用户>   — 开盒指定用户
      /开盒 ...          — /盒 的中文别名（通过 match() 实现）
    """

    command_name: str = "盒"
    command_description: str = "开盒指定用户，生成信息卡片图片"
    permission_level: PermissionLevel = PermissionLevel.USER
    chat_type: ChatType = ChatType.ALL

    plugin: "BoxPlugin"

    # ------------------------------------------------------------------ #
    # 命令匹配：同时支持 “盒” 与 “开盒”
    # ------------------------------------------------------------------ #

    @classmethod
    def match(cls, parts: list[str]) -> int:
        """匹配命令名，同时支持 “盒” 和 “开盒”。"""
        if not parts:
            return 0
        if parts[0] in ("盒", "开盒"):
            return 1
        return 0

    # ------------------------------------------------------------------ #
    # 路由
    # ------------------------------------------------------------------ #

    @cmd_route()
    async def handle_root(self, target: str = "") -> tuple[bool, str]:
        """开盒主入口。

        Args:
            target: 目标用户标识，可以是 QQ 号或 @<昵称:QQ号> 格式
        """
        return await self._do_box(target)

    # ------------------------------------------------------------------ #
    # 业务逻辑
    # ------------------------------------------------------------------ #

    async def _reply(self, text: str) -> None:
        """向当前流发送文本消息。"""
        from src.app.plugin_system.api.send_api import send_text

        await send_text(text, stream_id=self.stream_id, reply_to=self.message_id or None)

    def _config(self) -> BoxPluginConfig:
        """读取插件配置。"""
        config = getattr(self.plugin, "config", None)
        if isinstance(config, BoxPluginConfig):
            return config
        return BoxPluginConfig()

    async def _resolve_target(self, target: str) -> str | None:
        """解析目标 QQ 号。

        Args:
            target: 命令参数

        Returns:
            目标 QQ 号字符串，无法解析时返回 None
        """
        target = target.strip()
        if not target:
            return None

        at_match = _AT_PATTERN.fullmatch(target)
        if at_match:
            return at_match.group(2).strip()

        if _QQ_PATTERN.fullmatch(target):
            return target

        return None

    async def _current_user_id(self) -> tuple[str, str]:
        """获取当前消息发送者的 (platform, user_id)。"""
        platform = ""
        user_id = ""
        if self._message is not None:
            platform = self._message.platform or ""
            user_id = self._message.sender_id or ""
        if not platform:
            info = await get_stream_info(self.stream_id)
            if isinstance(info, dict):
                platform = info.get("platform") or ""
        return platform, str(user_id)

    async def _current_group_id(self) -> str:
        """获取当前流的群 ID，如果是私聊则返回空串。"""
        info = await get_stream_info(self.stream_id)
        if not isinstance(info, dict):
            return ""
        if info.get("chat_type") != "group":
            return ""
        return str(info.get("group_id") or "")

    async def _do_box(self, target_arg: str) -> tuple[bool, str]:
        """执行开盒。"""
        plugin = self.plugin
        if plugin.box_core is None:
            await self._reply("开盒插件未正确加载：核心模块未初始化")
            return False, "core not ready"

        platform, sender_id = await self._current_user_id()
        if not sender_id:
            await self._reply("无法确定当前用户身份")
            return False, "no sender"

        group_id = await self._current_group_id()

        # 解析目标
        target_id = await self._resolve_target(target_arg)
        if not target_id:
            if group_id:
                await self._reply("请 @ 一个用户或提供 QQ 号来开盒")
                return False, "missing target in group"
            target_id = sender_id

        # 检查权限：only_admin
        config = self._config()
        is_admin = False
        if platform:
            try:
                person_id = permission_api.generate_person_id(platform, sender_id)
                level = await permission_api.get_user_permission_level(person_id)
                is_admin = level >= PermissionLevel.OPERATOR
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"获取用户权限级别失败: {exc}")

        if config.basic.only_admin and not is_admin and target_id != sender_id:
            await self._reply("仅管理员可以开盒他人")
            return True, "permission denied"

        # 检查保护名单
        protect_ids = {str(pid) for pid in config.protection.protect_ids}
        # Bot 自身自动保护（通过 adapter 获取 bot_id）
        try:
            login_resp = await send_adapter_command(
                adapter_sign=config.adapter.adapter_signature,
                command_name="get_login_info",
                command_data={},
                timeout=config.adapter.api_timeout,
            )
            bot_id = str(((login_resp or {}).get("data") or {}).get("user_id") or "")
            if bot_id:
                protect_ids.add(bot_id)
        except Exception:  # noqa: BLE001
            pass

        if target_id in protect_ids and target_id != sender_id:
            await self._reply("该用户受到保护，无法开盒")
            return True, "target protected"

        # 执行开盒
        try:
            image_data = await plugin.box_core.box_user(
                target_id=target_id,
                group_id=group_id,
                sender_id=sender_id,
                is_admin=is_admin,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"开盒失败: {exc}", exc_info=True)
            await self._reply(f"开盒失败：{exc}")
            return False, "exception"

        if not image_data:
            await self._reply("开盒失败：无法获取该用户信息")
            return False, "no image"

        image_b64 = base64.b64encode(image_data).decode("utf-8")
        await send_image(
            image_data=image_b64,
            stream_id=self.stream_id,
            reply_to=self.message_id or None,
        )

        # 自动撤回（暂不实现实际撤回 API；保留延迟日志占位）
        recall_time = config.recall.recall_time
        if recall_time > 0:
            asyncio.create_task(self._delayed_recall_log(recall_time, target_id))

        return True, "ok"

    async def _delayed_recall_log(self, seconds: int, target_id: str) -> None:
        """占位实现：等待固定秒数后打日志。

        实际撤回 API 因 neo-mofox 当前未提供统一接口，留待后续按平台适配。
        """
        try:
            await asyncio.sleep(seconds)
            logger.info(f"开盒卡片（target={target_id}）应在此时撤回（暂未实现实际撤回）")
        except asyncio.CancelledError:
            pass
