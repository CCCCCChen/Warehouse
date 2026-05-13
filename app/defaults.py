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

DEFAULT_TYPE_TREE = {
    "家电": ["大家电", "小家电", "厨卫电器", "环境电器"],
    "家具": ["客厅家具", "餐厅家具", "卧室家具", "书房家具", "储物家具"],
    "家纺": ["床品", "毯子", "毛巾浴巾", "地毯地垫", "其他"],
    "厨具餐具": ["炊具", "刀具砧板", "餐具", "水具", "烘焙工具"],
    "食品": ["主食", "调味料", "零食", "饮料", "冷冻食品", "干货"],
    "日化清洁": ["个人洗护", "家庭清洁", "卫浴用品", "其他"],
    "工具五金": ["手动工具", "电动工具", "五金耗材", "维修配件"],
    "电子产品": ["数码设备", "影音设备", "网络设备", "存储设备", "充电设备"],
    "书籍": ["文学小说", "社科历史", "专业书籍", "生活艺术", "儿童绘本", "期刊杂志"],
    "药品": ["内服药", "外用药", "医疗器械", "保健品", "家庭急救包"],
    "文件证件": ["身份证明", "学历证明", "资产证明", "合同票据", "医疗档案"],
    "纪念品": ["旅行纪念", "礼物收藏", "手工DIY", "奖杯证书"],
    "宠物用品": ["食品", "餐具", "寝具", "清洁", "出行", "玩具"],
    "其他": ["其他"],
}

DEFAULT_ROOMS = ["玄关", "厨房", "客厅", "过道", "厕所", "房间1", "房间2", "房间3", "阳台", "其他"]
DEFAULT_SPOTS = ["整面墙", "柜子", "抽屉", "台面", "床底", "冰箱", "收纳箱", "置物架", "其他"]
DEFAULT_RESPONSIBLE_PEOPLE = ["我"]


def default_config_json() -> tuple[str, str, str]:
    return (
        json.dumps(DEFAULT_CATEGORIES, ensure_ascii=False),
        json.dumps(DEFAULT_LOCATIONS, ensure_ascii=False),
        json.dumps(DEFAULT_UNITS, ensure_ascii=False),
    )


def default_extended_config_json() -> dict:
    categories_json, locations_json, units_json = default_config_json()
    return {
        "categories_json": categories_json,
        "locations_json": locations_json,
        "units_json": units_json,
        "type_tree_json": json.dumps(DEFAULT_TYPE_TREE, ensure_ascii=False),
        "rooms_json": json.dumps(DEFAULT_ROOMS, ensure_ascii=False),
        "spots_json": json.dumps(DEFAULT_SPOTS, ensure_ascii=False),
        "responsible_people_json": json.dumps(DEFAULT_RESPONSIBLE_PEOPLE, ensure_ascii=False),
        "area_map_json": json.dumps([], ensure_ascii=False),
    }
