from src.plugin_system import BaseEventHandler, EventType
from src.plugin_system.base.base_event import HandlerResult
from src.common.logger import get_logger
from typing import Dict, Any

logger = get_logger("box_plugin.handler")

class GroupMemberHandler(BaseEventHandler):
    """群成员事件处理器"""
    handler_name = "box_group_member_handler"
    handler_description = "处理群成员事件，自动开盒"
    weight = 10
    intercept_message = False
    init_subscribe = [EventType.ON_NOTICE_RECEIVED]
    
    async def execute(self, params: Dict[str, Any]) -> HandlerResult:
        """处理群成员事件"""
        try:
            # 获取事件类型
            event_type = params.get("event_type")
            group_id = params.get("group_id")
            user_id = params.get("user_id")
            
            # 检查是否为群成员相关事件
            # 由于当前适配器未实现群成员增加/减少事件，这里仅作占位
            if event_type not in [EventType.ON_NOTICE_RECEIVED]:
                return HandlerResult(success=True, continue_process=True)
            
            # 检查群聊白名单
            auto_box_groups = self.get_config("groups.auto_box_groups", [])
            if auto_box_groups and group_id not in auto_box_groups:
                return HandlerResult(success=True, continue_process=True)
            
            # 检查保护名单
            protect_ids = self.get_config("protection.protect_ids", [])
            if user_id in protect_ids:
                return HandlerResult(success=True, continue_process=True)
            
            # 执行自动开盒
            await self._auto_box_user(user_id, group_id, event_type)
            
            return HandlerResult(success=True, continue_process=True)
        except Exception as e:
            logger.error(f"处理群成员事件失败: {e}")
            return HandlerResult(success=False, message=str(e), continue_process=True)
    
    async def _auto_box_user(self, user_id: str, group_id: str, event_type: str):
        """自动开盒用户"""
        # 获取插件实例
        from src.plugin_system import PluginManager
        plugin = PluginManager.get_plugin("box_plugin")
        
        if not plugin or not plugin.box_core:
            logger.error("开盒插件未正确加载")
            return
            
        # 执行开盒
        image_data = await plugin.box_core.box_user(
            user_id,
            group_id or "",
            user_id,  # sender_id设为用户自己
            False  # 非管理员
        )
        
        if not image_data:
            logger.error(f"自动开盒用户 {user_id} 失败")
            return
            
        # 发送图片到群聊
        # 注意：这里需要适配MoFox的API来发送消息到指定群聊
        logger.info(f"自动开盒用户 {user_id} 成功，图片已生成")
        
        # 在实际实现中，这里会调用发送消息的API
        # 例如：await self.send_group_image(group_id, image_data)