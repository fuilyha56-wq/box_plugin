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
            # 为每个显示选项创建配置字段，使用英文键名
            "qq_number": ConfigField(
                type=bool,
                default=True,
                description="显示QQ号"
            ),
            "nickname": ConfigField(
                type=bool,
                default=True,
                description="显示昵称"
            ),
            "remark": ConfigField(
                type=bool,
                default=True,
                description="显示备注"
            ),
            "group_nickname": ConfigField(
                type=bool,
                default=True,
                description="显示群昵称"
            ),
            "group_title": ConfigField(
                type=bool,
                default=True,
                description="显示群头衔"
            ),
            "gender": ConfigField(
                type=bool,
                default=True,
                description="显示性别"
            ),
            "birthday": ConfigField(
                type=bool,
                default=True,
                description="显示生日"
            ),
            "constellation": ConfigField(
                type=bool,
                default=True,
                description="显示星座"
            ),
            "zodiac": ConfigField(
                type=bool,
                default=True,
                description="显示生肖"
            ),
            "age": ConfigField(
                type=bool,
                default=True,
                description="显示年龄"
            ),
            "blood_type": ConfigField(
                type=bool,
                default=True,
                description="显示血型"
            ),
            "phone": ConfigField(
                type=bool,
                default=True,
                description="显示电话"
            ),
            "email": ConfigField(
                type=bool,
                default=True,
                description="显示邮箱"
            ),
            "hometown": ConfigField(
                type=bool,
                default=True,
                description="显示家乡"
            ),
            "address": ConfigField(
                type=bool,
                default=True,
                description="显示现居"
            ),
            "career": ConfigField(
                type=bool,
                default=True,
                description="显示职业"
            ),
            "tags": ConfigField(
                type=bool,
                default=True,
                description="显示个性标签"
            ),
            "risky_account": ConfigField(
                type=bool,
                default=True,
                description="显示风险账号"
            ),
            "robot_account": ConfigField(
                type=bool,
                default=True,
                description="显示机器人账号"
            ),
            "qq_vip": ConfigField(
                type=bool,
                default=True,
                description="显示QQVIP"
            ),
            "year_vip": ConfigField(
                type=bool,
                default=True,
                description="显示年VIP"
            ),
            "vip_level": ConfigField(
                type=bool,
                default=True,
                description="显示VIP等级"
            ),
            "group_level": ConfigField(
                type=bool,
                default=True,
                description="显示群等级"
            ),
            "join_time": ConfigField(
                type=bool,
                default=True,
                description="显示加群时间"
            ),
            "qq_level": ConfigField(
                type=bool,
                default=True,
                description="显示QQ等级"
            ),
            "reg_time": ConfigField(
                type=bool,
                default=True,
                description="显示注册时间"
            ),
            "signature": ConfigField(
                type=bool,
                default=True,
                description="显示签名"
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