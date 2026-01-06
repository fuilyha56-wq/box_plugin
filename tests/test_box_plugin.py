"""
开盒插件测试文件
"""

def test_plugin_structure():
    """测试插件基本结构"""
    # 测试导入
    try:
        from plugins.box_plugin import metadata
        print("✓ 插件元数据导入成功")
    except ImportError as e:
        print(f"✗ 插件元数据导入失败: {e}")
        return False
    
    # 测试插件主类
    try:
        from plugins.box_plugin.plugin import BoxPlugin
        print("✓ 插件主类导入成功")
    except ImportError as e:
        print(f"✗ 插件主类导入失败: {e}")
        return False
    
    # 测试命令组件
    try:
        from plugins.box_plugin.commands.box_command import BoxCommand
        print("✓ 命令组件导入成功")
    except ImportError as e:
        print(f"✗ 命令组件导入失败: {e}")
        return False
    
    # 测试事件处理器
    try:
        from plugins.box_plugin.handlers.group_member_handler import GroupMemberHandler
        print("✓ 事件处理器导入成功")
    except ImportError as e:
        print(f"✗ 事件处理器导入失败: {e}")
        return False
    
    # 测试核心模块
    try:
        from plugins.box_plugin.core.box_core import BoxCore
        from plugins.box_plugin.core.draw import CardMaker
        from plugins.box_plugin.core.field_mapping import FIELD_MAPPING
        from plugins.box_plugin.core.utils import get_avatar
        print("✓ 核心模块导入成功")
    except ImportError as e:
        print(f"✗ 核心模块导入失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开盒插件结构测试")
    print("=" * 30)
    
    if test_plugin_structure():
        print("=" * 30)
        print("✓ 所有测试通过，插件结构完整")
    else:
        print("=" * 30)
        print("✗ 测试失败，插件结构存在问题")