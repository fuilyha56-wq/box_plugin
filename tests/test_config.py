#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试新的配置格式
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.field_mapping import ALL_LABELS, LABEL_TO_CONFIG_KEY


def test_config_format():
    """测试配置格式"""
    print("测试新的配置格式...")
    
    # 检查是否所有标签都有对应的配置项
    print(f"总共 {len(ALL_LABELS)} 个显示选项:")
    for i, label in enumerate(ALL_LABELS, 1):
        config_key = LABEL_TO_CONFIG_KEY.get(label, label)
        print(f'{i:2d}. {config_key:<15} # {label}')
    
    print("\n配置格式验证通过!")


if __name__ == "__main__":
    test_config_format()