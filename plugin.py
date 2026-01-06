from src.plugin_system import (
    BasePlugin,
    register_plugin,
    ComponentInfo,
    ConfigField
)
from src.plugin_system.base.component_types import PermissionNodeField
from src.common.logger import get_logger

# 导入组件
from .commands.box_command import BoxCommand
from .handlers.group_member_handler import GroupMemberHandler

logger = get_logger("box_plugin")

@register_plugin
class BoxPlugin(BasePlugin):
    """开盒插件主类"""
    
    plugin_name = "box_plugin"
    enable_plugin = True
    dependencies = []
    python_dependencies = ["Pillow", "emoji", "zhdate"]
    config_file_name = "config.toml"
    
    # 配置section描述
    config_section_descriptions = {
        "basic": "基础设置",
        "groups": "群组设置",
        "protection": "保护设置",
        "display": "显示设置",
        "recall": "撤回设置",
        "library": "高级设置",
    }
    
    # 配置文件结构定义
    config_schema = {
        "basic": {
            "only_admin": ConfigField(
                type=bool,
                default=False,
                description="仅bot管理员可开盒他人",
                hint="但自己开盒自己不受限制"
            ),
            "clean_cache": ConfigField(
                type=bool,
                default=False,
                description="重载插件时清空缓存",
                hint="当插件重载时，清空缓存的开盒卡片"
            ),
        },
        "groups": {
            "auto_box_groups": ConfigField(
                type=list,
                default=[],
                description="自动开盒群聊白名单",
                hint="只自动开盒白名单群聊的新群友/主动退群的人，不填则默认所有群聊都启用自动开盒"
            ),
        },
        "protection": {
            "protect_ids": ConfigField(
                type=list,
                default=[],
                description="信息保护用户",
                hint="开盒时，会忽略黑名单中的用户，注意：Bot和Bot管理员已默认被保护，除非Bot管理员亲自使用命令盒自己，否则无法被开盒"
            ),
        },
        "display": {
            "display_options": ConfigField(
                type=list,
                default=[
                    "QQ号", "昵称", "备注", "群昵称", "群头衔", "性别", "生日", "星座", "生肖", 
                    "年龄", "血型", "电话", "邮箱", "家乡", "现居", "职业", "个性标签", 
                    "风险账号", "机器人账号", "QQVIP", "年VIP", "VIP等级", "群等级", 
                    "加群时间", "QQ等级", "注册时间", "签名"
                ],
                description="信息显示选项",
                hint="选择要显示的信息字段",
                choices=[
                    "QQ号", "昵称", "备注", "群昵称", "群头衔", "性别", "生日", "星座", "生肖", 
                    "年龄", "血型", "电话", "邮箱", "家乡", "现居", "职业", "个性标签", 
                    "风险账号", "机器人账号", "QQVIP", "年VIP", "VIP等级", "群等级", 
                    "加群时间", "QQ等级", "注册时间", "签名"
                ]
            ),
        },
        "recall": {
            "recall_time": ConfigField(
                type=int,
                default=10,
                description="撤回时间(秒)",
                hint="几秒后撤回开盒卡片，设为 0 则不撤回",
                min=0,
                max=110
            ),
        },
        "library": {
            "cookie": ConfigField(
                type=str,
                default="",
                description="Library Cookie",
                hint="高级配置，普通用户无需填写",
                input_type="password"
            ),
            "desensitize": ConfigField(
                type=bool,
                default=False,
                description="去敏化",
                hint="高级配置，普通用户无需填写"
            ),
            "recall_desen_time": ConfigField(
                type=int,
                default=5,
                description="敏感撤回时间",
                hint="高级配置，普通用户无需填写",
                min=0,
                max=110
            ),
        }
    }
    
    # 权限节点定义
    permission_nodes = [
        PermissionNodeField(
            node_name="can_box",
            description="允许使用开盒功能"
        ),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.box_core = None
        
    async def on_plugin_loaded(self):
        """插件加载完成后的回调"""
        try:
            # 初始化开盒核心
            from .core.box_core import BoxCore
            self.box_core = BoxCore(self.plugin_dir, self.get_config)
            logger.info("开盒插件已加载，box_core初始化完成")
        except Exception as e:
            logger.error(f"开盒插件加载失败: {e}")
            self.box_core = None
        
    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """注册插件的所有功能组件"""
        return [
            (BoxCommand.get_plus_command_info(), BoxCommand),
            (GroupMemberHandler.get_handler_info(), GroupMemberHandler),
        ]
        
    async def on_plugin_unloaded(self):
        """插件卸载时的回调"""
        if self.box_core:
            await self.box_core.cleanup()