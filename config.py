"""Box Plugin 插件配置。

提供基础开关、自动开盒群配置、保护名单、字段显示开关、撤回与字体下载配置。
"""

from __future__ import annotations

from typing import ClassVar

from src.app.plugin_system.base import BaseConfig, Field, SectionBase, config_section


# 默认字体下载地址（jsDelivr 镜像 GitHub Raw，可在 config 中覆盖）
DEFAULT_CUTE_FONT_URL: str = (
    "https://cdn.jsdelivr.net/gh/Zhalslar/astrbot_plugin_box@main/core/resource/"
    "%E5%8F%AF%E7%88%B1%E5%AD%97%E4%BD%93.ttf"
)
DEFAULT_EMOJI_FONT_URL: str = (
    "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@main/fonts/NotoColorEmoji.ttf"
)
# 拉丁/俄语/希腊等 fallback（Noto Sans Regular，825 KB）
DEFAULT_LATIN_FONT_URL: str = (
    "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io@main/fonts/NotoSans/full/ttf/"
    "NotoSans-Regular.ttf"
)
# 韩语/日语假名 fallback（Noto Sans KR Subset，4.5 MB）
DEFAULT_CJK_KR_FONT_URL: str = (
    "https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main/Sans/SubsetOTF/KR/"
    "NotoSansKR-Regular.otf"
)


class BoxPluginConfig(BaseConfig):
    """Box Plugin 配置。"""

    config_name: ClassVar[str] = "config"
    config_description: ClassVar[str] = "Box Plugin 开盒插件配置"

    @config_section("plugin", title="插件设置", tag="plugin")
    class PluginSection(SectionBase):
        """插件级开关。"""

        enabled: bool = Field(
            default=True,
            description="是否启用 Box Plugin",
            label="启用插件",
            tag="plugin",
        )
        version: str = Field(
            default="2.0.0",
            description="插件版本",
            label="插件版本",
            disabled=True,
            tag="general",
        )

    @config_section("basic", title="基础设置", tag="plugin")
    class BasicSection(SectionBase):
        """基础行为。"""

        only_admin: bool = Field(
            default=False,
            description="是否仅 Bot 管理员可开盒他人（开盒自己不受限制）",
            label="仅管理员可开盒他人",
            tag="security",
        )
        clean_cache: bool = Field(
            default=False,
            description="插件卸载/重载时是否清空缓存的开盒卡片",
            label="重载时清空缓存",
            tag="performance",
        )

    @config_section("groups", title="自动开盒群组", tag="plugin")
    class GroupsSection(SectionBase):
        """自动开盒群聊白名单。"""

        auto_box_groups: list[str] = Field(
            default_factory=list,
            description="自动开盒群聊白名单；留空表示所有群启用入群/退群自动开盒",
            label="自动开盒群白名单",
            input_type="list",
            item_type="str",
            tag="general",
        )

    @config_section("protection", title="保护设置", tag="security")
    class ProtectionSection(SectionBase):
        """信息保护名单。"""

        protect_ids: list[str] = Field(
            default_factory=list,
            description="信息保护用户名单。Bot 自身会自动加入保护名单",
            label="保护用户 ID",
            input_type="list",
            item_type="str",
            tag="security",
        )

    @config_section("display", title="字段显示开关", tag="display")
    class DisplaySection(SectionBase):
        """字段显示开关。"""

        qq_number: bool = Field(default=True, description="显示 QQ 号", label="QQ 号", tag="display")
        nickname: bool = Field(default=True, description="显示昵称", label="昵称", tag="display")
        remark: bool = Field(default=True, description="显示备注", label="备注", tag="display")
        group_nickname: bool = Field(default=True, description="显示群昵称", label="群昵称", tag="display")
        group_title: bool = Field(default=True, description="显示群头衔", label="群头衔", tag="display")
        gender: bool = Field(default=True, description="显示性别", label="性别", tag="display")
        birthday: bool = Field(default=True, description="显示生日", label="生日", tag="display")
        constellation: bool = Field(default=True, description="显示星座", label="星座", tag="display")
        zodiac: bool = Field(default=True, description="显示生肖", label="生肖", tag="display")
        age: bool = Field(default=True, description="显示年龄", label="年龄", tag="display")
        blood_type: bool = Field(default=True, description="显示血型", label="血型", tag="display")
        phone: bool = Field(default=False, description="显示电话", label="电话", tag="display")
        email: bool = Field(default=False, description="显示邮箱", label="邮箱", tag="display")
        hometown: bool = Field(default=True, description="显示家乡", label="家乡", tag="display")
        address: bool = Field(default=True, description="显示现居", label="现居", tag="display")
        career: bool = Field(default=True, description="显示职业", label="职业", tag="display")
        tags: bool = Field(default=True, description="显示个性标签", label="个性标签", tag="display")
        risky_account: bool = Field(default=True, description="显示风险账号", label="风险账号", tag="display")
        robot_account: bool = Field(default=True, description="显示机器人账号", label="机器人账号", tag="display")
        qq_vip: bool = Field(default=True, description="显示 QQVIP", label="QQVIP", tag="display")
        year_vip: bool = Field(default=True, description="显示年 VIP", label="年 VIP", tag="display")
        vip_level: bool = Field(default=True, description="显示 VIP 等级", label="VIP 等级", tag="display")
        group_level: bool = Field(default=True, description="显示群等级", label="群等级", tag="display")
        join_time: bool = Field(default=True, description="显示加群时间", label="加群时间", tag="display")
        qq_level: bool = Field(default=True, description="显示 QQ 等级", label="QQ 等级", tag="display")
        reg_time: bool = Field(default=True, description="显示注册时间", label="注册时间", tag="display")
        signature: bool = Field(default=True, description="显示签名", label="签名", tag="display")

    @config_section("recall", title="撤回设置", tag="general")
    class RecallSection(SectionBase):
        """卡片撤回时间。"""

        recall_time: int = Field(
            default=0,
            description="开盒卡片发送后多少秒撤回，0 表示不撤回",
            label="撤回秒数",
            ge=0,
            le=120,
            tag="general",
        )

    @config_section("adapter", title="适配器设置", tag="ai")
    class AdapterSection(SectionBase):
        """适配器调用配置。"""

        adapter_signature: str = Field(
            default="napcat_adapter:adapter:napcat_adapter",
            description="用于查询用户信息的 Adapter 组件签名，默认使用 napcat_adapter",
            label="Adapter 签名",
            tag="ai",
        )
        api_timeout: float = Field(
            default=20.0,
            description="调用适配器 API 的超时秒数",
            label="API 超时",
            ge=1.0,
            le=120.0,
            tag="performance",
        )

    @config_section("font", title="字体资源", tag="general")
    class FontSection(SectionBase):
        """字体资源下载配置。

        字体文件不再随插件分发，首次运行时按需下载到 plugin_dir/data/fonts/。
        """

        cute_font_url: str = Field(
            default=DEFAULT_CUTE_FONT_URL,
            description="可爱中文字体 (.ttf) 下载地址",
            label="中文字体 URL",
            tag="general",
        )
        emoji_font_url: str = Field(
            default=DEFAULT_EMOJI_FONT_URL,
            description="Emoji 字体 (.ttf) 下载地址；下载失败将自动回退到中文字体绘制 emoji",
            label="Emoji 字体 URL",
            tag="general",
        )
        download_timeout: float = Field(
            default=30.0,
            description="字体下载超时秒数",
            label="下载超时",
            ge=5.0,
            le=300.0,
            tag="performance",
        )
        skip_emoji_font: bool = Field(
            default=False,
            description="是否跳过 Emoji 字体下载（仅使用中文字体绘制所有字符）",
            label="跳过 Emoji 字体",
            tag="general",
        )
        latin_font_url: str = Field(
            default=DEFAULT_LATIN_FONT_URL,
            description="拉丁/俄语/希腊语 fallback 字体 (.ttf/.otf)，覆盖日文/俄文名等",
            label="Latin Fallback 字体 URL",
            tag="general",
        )
        cjk_kr_font_url: str = Field(
            default=DEFAULT_CJK_KR_FONT_URL,
            description="韩语/日语假名 fallback 字体 (.otf)，覆盖韩文昵称等",
            label="韩语/日语 Fallback 字体 URL",
            tag="general",
        )

    plugin: PluginSection = Field(default_factory=PluginSection)
    basic: BasicSection = Field(default_factory=BasicSection)
    groups: GroupsSection = Field(default_factory=GroupsSection)
    protection: ProtectionSection = Field(default_factory=ProtectionSection)
    display: DisplaySection = Field(default_factory=DisplaySection)
    recall: RecallSection = Field(default_factory=RecallSection)
    adapter: AdapterSection = Field(default_factory=AdapterSection)
    font: FontSection = Field(default_factory=FontSection)
