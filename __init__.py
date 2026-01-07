from src.plugin_system.base.plugin_metadata import PluginMetadata, PythonDependency

__plugin_meta__ = PluginMetadata(
    name="开盒插件",
    description="利用Onebot协议的接口获取QQ用户信息,并以图片形式展示",
    usage="""
    命令：
    - /盒 [@某人|QQ号] - 开盒指定用户
    - /开盒 [@某人|QQ号] - 开盒指定用户
    
    功能：
    - 获取用户基本信息（QQ号、昵称、备注等）
    - 获取用户群信息（群昵称、群头衔、群等级等）
    - 获取用户个人资料（性别、年龄、生日、星座等）
    - 获取用户联系方式（电话、邮箱等）
    - 获取用户地理位置信息（家乡、现居地等）
    - 获取用户职业、标签等信息
    - 获取用户QQ会员信息（QQVIP、年VIP、VIP等级等）
    - 获取用户QQ等级信息
    - 获取用户注册时间、加群时间等
    - 获取用户签名信息
    - 支持自定义显示字段
    - 支持自动撤回（可配置）
    - 支持保护名单（防止被开盒）
    """,
    version="1.1.0",
    author="ikun两年半",
    license="AGPL",
    repository_url="https://github.com/ikun-11451/box_plugin",
    keywords=["开盒", "QQ信息", "用户信息", "娱乐"],
    categories=["娱乐", "信息"],
    python_dependencies=[
        PythonDependency(
            package_name="PIL",
            install_name="Pillow",
            version=">=9.0.0",
            description="图片处理库，用于生成开盒卡片"
        ),
        PythonDependency(
            package_name="emoji",
            version=">=2.0.0",
            description="Emoji处理库，用于显示Emoji"
        ),
        PythonDependency(
            package_name="zhdate",
            version=">=0.1.0",
            description="农历日期处理库，用于计算生肖"
        )
    ],
    dependencies=[],
    type=None,
    extra={
        "is_built_in": False,
        "plugin_type": "entertainment",
    },
)