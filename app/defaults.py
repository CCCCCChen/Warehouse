import json


DEFAULT_CATEGORIES = [
    "厨房-食材",
    "厨房-调味",
    "厨房-饮品",
    "清洁-洗护",
    "清洁-家务",
    "卫浴-洗漱",
    "卫浴-纸品",
    "日用-收纳",
    "日用-文具",
    "家电-耗材",
    "药品-常备",
    "母婴-用品",
    "宠物-用品",
    "其他",
]

DEFAULT_LOCATIONS = [
    "厨房-冰箱",
    "厨房-橱柜",
    "厨房-台面",
    "客厅-柜子",
    "卧室-衣柜",
    "卫生间-柜子",
    "阳台-储物",
    "杂物间",
    "车里",
    "其他",
]

DEFAULT_UNITS = ["个", "件", "袋", "瓶", "盒", "包", "卷", "罐", "支", "片", "kg", "g", "L", "ml"]


def default_config_json() -> tuple[str, str, str]:
    return (
        json.dumps(DEFAULT_CATEGORIES, ensure_ascii=False),
        json.dumps(DEFAULT_LOCATIONS, ensure_ascii=False),
        json.dumps(DEFAULT_UNITS, ensure_ascii=False),
    )

