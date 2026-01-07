from src.plugin_system import (
    PlusCommand,
    CommandArgs,
    ChatType,
    plugin_manage_api,
)
from src.plugin_system.utils.permission_decorators import require_permission
from src.plugin_system.apis.permission_api import permission_api
from src.common.logger import get_logger
from typing import Tuple, Optional
import asyncio

logger = get_logger("box_plugin.command")

class BoxCommand(PlusCommand):
    """开盒命令"""
    command_name = "盒"
    command_description = "开盒指定用户，获取其详细信息"
    command_aliases = ["开盒"]
    priority = 5
    chat_type_allow = ChatType.ALL
    intercept_message = True
    
    @require_permission("plugins.box_plugin.can_box")
    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        """执行开盒命令"""
        # 获取目标用户ID
        target_id = None
        group_id = None
        
        # 从参数中获取目标用户ID
        if args.get_raw():
            # 检查是否有@某人
            if hasattr(self.message, "message_segments"):
                for segment in self.message.message_segments:
                    if segment.get("type") == "at":
                        # 尝试多种可能的字段名来获取用户ID
                        data = segment.get("data", {})
                        target_id = (data.get("qq") or
                                   data.get("user_id") or
                                   data.get("target"))
                        if target_id is not None:
                            target_id = str(target_id)
                        break
                    elif segment.get("type") == "text":
                        # 检查文本中是否有QQ号或特殊格式的用户ID
                        text = segment.get("data", {}).get("text", "")
                        # 检查是否是 @<昵称:QQ号> 格式
                        if text.startswith("@<") and text.endswith(">") and ":" in text:
                            # 尝试解析 @<昵称:QQ号> 格式
                            try:
                                # 提取QQ号部分
                                parts = text[2:-1].split(":")
                                if len(parts) == 2:
                                    potential_id = parts[1]
                                    if potential_id.isdigit() and len(potential_id) >= 5 and len(potential_id) <= 11:
                                        target_id = potential_id
                            except Exception:
                                pass
                        # 检查是否是纯数字QQ号
                        elif text.isdigit() and len(text) >= 5 and len(text) <= 11:
                            target_id = text
                        break
            else:
                # 如果没有message_segments，直接从参数中获取QQ号
                text = args.get_raw().strip()
                # 检查是否是 @<昵称:QQ号> 格式
                if text.startswith("@<") and text.endswith(">") and ":" in text:
                    # 尝试解析 @<昵称:QQ号> 格式
                    try:
                        # 提取QQ号部分
                        parts = text[2:-1].split(":")
                        if len(parts) == 2:
                            potential_id = parts[1]
                            if potential_id.isdigit() and len(potential_id) >= 5 and len(potential_id) <= 11:
                                target_id = potential_id
                    except Exception:
                        pass
                # 检查是否是纯数字QQ号
                elif text.isdigit() and len(text) >= 5 and len(text) <= 11:
                    target_id = text
        
        # 如果没有指定目标，检查是否是群聊环境
        if not target_id:
            # 在群聊中，如果没有@任何人且没有提供QQ号，则提示用户
            if hasattr(self.message, "group_info") and self.message.group_info is not None:
                await self.send_text("请@一个用户或提供QQ号来开盒")
                return True, "未指定目标用户", True
            else:
                # 在私聊中，默认为自己开盒
                target_id = self.message.user_info.user_id
            
        # 获取群ID（如果是群聊）
        if hasattr(self.message, "group_info") and self.message.group_info is not None:
            group_id = self.message.group_info.group_id
            
        # 检查权限
        only_admin = self.get_config("basic.only_admin", False)
        is_admin = await permission_api.is_master(self.message.user_info.platform, self.message.user_info.user_id)
        if only_admin and not is_admin and target_id != self.message.user_info.user_id:
            await self.send_text("仅管理员可以开盒他人")
            return True, "权限不足", True
            
        # 检查保护名单
        protect_ids = self.get_config("protection.protect_ids", [])
        # 获取bot的QQ账号并加入保护名单
        from src.plugin_system.apis.config_api import get_global_config
        bot_qq = str(get_global_config("bot.qq_account", ""))
        if bot_qq and bot_qq not in protect_ids:
            protect_ids.append(bot_qq)
        if target_id in protect_ids and target_id != self.message.user_info.user_id:
            await self.send_text("该用户受到保护，无法开盒")
            return True, "目标用户受保护", True
            
        # 执行开盒操作
        try:
            await self._perform_box(target_id, group_id, args, is_admin)
            return True, "开盒成功", True
        except Exception as e:
            logger.error(f"开盒失败: {e}")
            await self.send_text(f"开盒失败: {str(e)}")
            return False, f"开盒失败: {str(e)}", True
    
    async def _perform_box(self, target_id: str, group_id: str, args: CommandArgs, is_admin: bool):
        """执行开盒操作"""
        # 获取插件实例
        plugin = plugin_manage_api.get_plugin_instance("box_plugin")
        
        if not plugin:
            logger.error("无法获取插件实例")
            await self.send_text("开盒插件未正确加载：无法获取插件实例")
            return
            
        if not plugin.box_core:
            logger.error("插件box_core未初始化")
            await self.send_text("开盒插件未正确加载：核心模块未初始化")
            return
            
        # 执行开盒
        image_data = await plugin.box_core.box_user(
            target_id,
            group_id or "",
            self.message.user_info.user_id,
            is_admin
        )
        
        if not image_data:
            await self.send_text("开盒失败，无法获取用户信息")
            return
            
        # 发送图片
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        await self.send_image(image_base64)
        
        # 检查是否需要撤回
        recall_time = self.get_config("recall.recall_time", 10)
        if recall_time > 0:
            # 在实际实现中，这里需要保存消息ID并创建撤回任务
            logger.info(f"将在{recall_time}秒后撤回开盒结果")