"""字段映射配置 —— 列表顺序决定开盒卡片的显示顺序。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# 辅助函数定义
def get_blood_type(num: int) -> str:
    """血型映射"""
    blood_types = {1: "A型", 2: "B型", 3: "O型", 4: "AB型", 5: "其他血型"}
    return blood_types.get(num, f"血型{num}")


def get_career(num: int) -> str:
    """职业映射"""
    career = {
        1: "计算机/互联网/通信",
        2: "生产/工艺/制造",
        3: "医疗/护理/制药",
        4: "金融/银行/投资/保险",
        5: "商业/服务业/个体经营",
        6: "文化/广告/传媒",
        7: "娱乐/艺术/表演",
        8: "律师/法务",
        9: "教育/培训",
        10: "公务员/行政/事业单位",
        11: "模特",
        12: "空姐",
        13: "学生",
        14: "其他职业",
    }
    return career.get(num, f"职业{num}")


def qqLevel_to_icon(level: int) -> str:
    """QQ等级图标映射"""
    icons = ["👑", "🌞", "🌙", "⭐"]
    levels = [64, 16, 4, 1]
    result = ""
    original_level = level
    for icon, lvl in zip(icons, levels):
        count, level = divmod(level, lvl)
        result += icon * count
    result += f"({original_level})"
    return result


def get_constellation(month: int, day: int) -> str:
    """星座映射"""
    constellations = {
        "白羊座": ((3, 21), (4, 19)),
        "金牛座": ((4, 20), (5, 20)),
        "双子座": ((5, 21), (6, 20)),
        "巨蟹座": ((6, 21), (7, 22)),
        "狮子座": ((7, 23), (8, 22)),
        "处女座": ((8, 23), (9, 22)),
        "天秤座": ((9, 23), (10, 22)),
        "天蝎座": ((10, 23), (11, 21)),
        "射手座": ((11, 22), (12, 21)),
        "摩羯座": ((12, 22), (1, 19)),
        "水瓶座": ((1, 20), (2, 18)),
        "双鱼座": ((2, 19), (3, 20)),
    }

    for constellation, (
        (start_month, start_day),
        (end_month, end_day),
    ) in constellations.items():
        if (month == start_month and day >= start_day) or (
            month == end_month and day <= end_day
        ):
            return constellation
        # 特别处理跨年星座
        if start_month > end_month:
            if (month == start_month and day >= start_day) or (
                month == end_month + 12 and day <= end_day
            ):
                return constellation
    return f"星座{month}-{day}"


def get_zodiac(year: int, month: int, day: int) -> str:
    """生肖映射"""
    from zhdate import ZhDate
    from datetime import date

    zodiacs = [
        "鼠🐀",
        "牛🐂",
        "虎🐅",
        "兔🐇",
        "龙🐉",
        "蛇🐍",
        "马🐎",
        "羊🐏",
        "猴🐒",
        "鸡🐔",
        "狗🐕",
        "猪🐖",
    ]

    current = date(year, month, day)

    try:
        # 获取该年农历正月初一的公历日期（春节）
        spring = ZhDate(year, 1, 1).to_datetime().date()
        # 决定生肖对应的年份
        zodiac_year = year if current >= spring else year - 1
    except (TypeError, AttributeError):
        # 如果农历日期超出范围（1900-2100）或其他错误，直接使用阳历年份
        zodiac_year = year

    # 生肖序号：2020年为鼠年
    index = (zodiac_year - 2020) % 12
    return zodiacs[index]


def parse_home_town(home_town_code: str) -> str:
    """家乡映射"""
    # 国家代码映射表（懒得查，欢迎提PR补充）
    country_map = {
        "49": "中国",
        "250": "俄罗斯",
        "222": "特里尔",
        "217": "法国",
    }
    # 中国省份（包括直辖市）代码映射表，由于不是一一对应，效果不佳
    province_map = {
        "98": "北京",
        "99": "天津/辽宁",
        "100": "冀/沪/吉",
        "101": "苏/豫/晋/黑/渝",
        "102": "浙/鄂/蒙/川",
        "103": "皖/湘/黔/陕",
        "104": "闽/粤/滇/甘/台",
        "105": "赣/桂/藏/青/港",
        "106": "鲁/琼/陕/宁/澳",
        "107": "新疆",
    }

    parts = home_town_code.split("-")
    if len(parts) < 3:
        return f"未知({home_town_code})"
        
    country_code, province_code, _ = parts[0], parts[1], parts[2]
    country = country_map.get(country_code, f"外国{country_code}")

    if country_code == "49":  # 中国
        if province_code != "0":
            province = province_map.get(province_code, f"{province_code}省")
            return province  # 只返回省份名
        else:
            return country  # 没有省份信息，返回国家名
    else:
        return country  # 不是中国，返回国家名

# 字段映射表：保持列表顺序即为显示顺序
# source: "info1" = stranger_info, "info2" = member_info, "computed" = 计算字段
FIELD_MAPPING: list[dict[str, Any]] = [
    {"key": "user_id", "label": "QQ号", "source": "info1"},
    {"key": "nickname", "label": "昵称", "source": "info1"},
    {"key": "remark", "label": "备注", "source": "info1"},
    {"key": "card", "label": "群昵称", "source": "info2"},
    {"key": "title", "label": "群头衔", "source": "info2"},
    {
        "key": "sex",
        "label": "性别",
        "source": "info1",
        "transform": lambda v: {"male": "男", "female": "女", "unknown": "未知"}.get(v, v),
    },
    {"key": "birthday", "label": "生日", "source": "computed"},
    {"key": "constellation", "label": "星座", "source": "computed"},
    {"key": "zodiac", "label": "生肖", "source": "computed"},
    {"key": "age", "label": "年龄", "source": "info1", "suffix": "岁"},
    {
        "key": "kBloodType",
        "label": "血型",
        "source": "info1",
        "transform": lambda v: get_blood_type(int(v)) if v and str(v).isdigit() else None,
    },
    {
        "key": "phoneNum",
        "label": "电话",
        "source": "info1",
        "skip_values": ["-", ""],
    },
    {
        "key": "eMail",
        "label": "邮箱",
        "source": "info1",
        "skip_values": ["-", ""],
    },
    {
        "key": "homeTown",
        "label": "家乡",
        "source": "info1",
        "transform": parse_home_town,
        "skip_values": ["0-0-0", ""],
    },
    {"key": "address", "label": "现居", "source": "computed"},
    {
        "key": "makeFriendCareer",
        "label": "职业",
        "source": "info1",
        "transform": lambda v: get_career(int(v)) if v and v != "0" and str(v).isdigit() else None,
        "skip_values": ["0", ""],
    },
    {"key": "labels", "label": "个性标签", "source": "info1"},
    {
        "key": "unfriendly",
        "label": "风险账号",
        "source": "info2",
        "transform": lambda v: "有" if v else None,
    },
    {
        "key": "is_robot",
        "label": "机器人账号",
        "source": "info2",
        "transform": lambda v: "是" if v else None,
    },
    {
        "key": "is_vip",
        "label": "QQVIP",
        "source": "info1",
        "transform": lambda v: "已开" if v else None,
    },
    {
        "key": "is_years_vip",
        "label": "年VIP",
        "source": "info1",
        "transform": lambda v: "已开" if v else None,
    },
    {
        "key": "vip_level",
        "label": "VIP等级",
        "source": "info1",
        "transform": lambda v: str(v) if v and str(v).isdigit() and int(v) != 0 else None,
    },
    {
        "key": "level",
        "label": "群等级",
        "source": "info2",
        "suffix": "级",
        "transform": lambda v: str(int(v)) if v and str(v).isdigit() else None,
    },
    {
        "key": "join_time",
        "label": "加群时间",
        "source": "info2",
        "transform": lambda v: datetime.fromtimestamp(int(v)).strftime("%Y-%m-%d")
        if v and str(v).isdigit()
        else None,
    },
    {
        "key": "qqLevel",
        "label": "QQ等级",
        "source": "info1",
        "transform": lambda v: qqLevel_to_icon(int(v)) if v and str(v).isdigit() else None,
    },
    {
        "key": "reg_time",
        "label": "注册时间",
        "source": "info1",
        "transform": lambda v: datetime.fromtimestamp(int(v)).strftime("%Y年")
        if v and str(v).isdigit()
        else None,
    },
    {
        "key": "long_nick",
        "label": "签名",
        "source": "info1",
        "multiline": True,
        "wrap_width": 15,
    },
]

# 中文名 -> 英文字段名 映射
LABEL_TO_KEY: dict[str, str] = {f["label"]: f["key"] for f in FIELD_MAPPING}

# 英文字段名 -> 中文名 映射
KEY_TO_LABEL: dict[str, str] = {f["key"]: f["label"] for f in FIELD_MAPPING}

# 所有可用的中文标签
ALL_LABELS: list[str] = [f["label"] for f in FIELD_MAPPING]

# 中文标签到英文配置键名的映射
LABEL_TO_CONFIG_KEY: dict[str, str] = {
    "QQ号": "qq_number",
    "昵称": "nickname",
    "备注": "remark",
    "群昵称": "group_nickname",
    "群头衔": "group_title",
    "性别": "gender",
    "生日": "birthday",
    "星座": "constellation",
    "生肖": "zodiac",
    "年龄": "age",
    "血型": "blood_type",
    "电话": "phone",
    "邮箱": "email",
    "家乡": "hometown",
    "现居": "address",
    "职业": "career",
    "个性标签": "tags",
    "风险账号": "risky_account",
    "机器人账号": "robot_account",
    "QQVIP": "qq_vip",
    "年VIP": "year_vip",
    "VIP等级": "vip_level",
    "群等级": "group_level",
    "加群时间": "join_time",
    "QQ等级": "qq_level",
    "注册时间": "reg_time",
    "签名": "signature",
}

# 英文配置键名到中文标签的映射
CONFIG_KEY_TO_LABEL: dict[str, str] = {v: k for k, v in LABEL_TO_CONFIG_KEY.items()}

# 英文配置键名（display section 字段名）-> 英文字段 key
CONFIG_KEY_TO_KEY: dict[str, str] = {
    config_key: LABEL_TO_KEY[label]
    for label, config_key in LABEL_TO_CONFIG_KEY.items()
    if label in LABEL_TO_KEY
}