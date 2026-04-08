# -*- coding: utf-8 -*-
"""
共享清洗工具函数与映射表。
所有 clean_*.py 模块通过 from ._common import ... 使用。
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

# ── 路径 ──
PROJ_ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = PROJ_ROOT / "data" / "delivery" / "tables"
DELIVERY_DIR = PROJ_ROOT / "data" / "delivery"

# ── 国家名 → ISO code 映射 ──
COUNTRY_CODE_MAP: dict[str, str] = {
    "美国": "US", "英国": "GB", "德国": "DE", "法国": "FR", "日本": "JP",
    "澳大利亚": "AU", "加拿大": "CA", "意大利": "IT", "西班牙": "ES",
    "荷兰": "NL", "比利时": "BE", "瑞士": "CH", "奥地利": "AT",
    "瑞典": "SE", "挪威": "NO", "丹麦": "DK", "芬兰": "FI", "爱尔兰": "IE",
    "波兰": "PL", "捷克": "CZ", "葡萄牙": "PT", "希腊": "GR",
    "韩国": "KR", "新加坡": "SG", "马来西亚": "MY", "泰国": "TH",
    "印度尼西亚": "ID", "菲律宾": "PH", "越南": "VN", "印度": "IN",
    "巴西": "BR", "墨西哥": "MX", "阿根廷": "AR", "智利": "CL",
    "哥伦比亚": "CO", "秘鲁": "PE", "南非": "ZA", "阿联酋": "AE",
    "沙特阿拉伯": "SA", "以色列": "IL", "土耳其": "TR", "埃及": "EG",
    "俄罗斯": "RU", "乌克兰": "UA", "罗马尼亚": "RO", "匈牙利": "HU",
    "新西兰": "NZ", "中国台湾": "TW", "中国香港": "HK", "柬埔寨": "KH",
    "尼日利亚": "NG", "肯尼亚": "KE", "巴基斯坦": "PK", "孟加拉国": "BD",
    "中国": "CN",
    "印尼": "ID",
    "突尼斯": "TN", "立陶宛": "LT", "科威特": "KW", "阿曼": "OM",
    "黎巴嫩": "LB", "保加利亚": "BG", "克罗地亚": "HR",
    "乌兹别克斯坦": "UZ", "危地马拉": "GT", "科索沃": "XK",
    "阿尔巴尼亚": "AL",
}

PRODUCT_LINE_MAP: dict[str, str] = {
    "吸奶器": "吸奶器", "消毒柜": "消毒柜", "消毒锅": "消毒柜",
    "暖奶器": "暖奶器", "辅食机": "辅食机",
    "智能监控": "智能监控", "喂养电器": "喂养电器", "家居出行": "家居出行",
    "unknown": "unknown", "": "unknown",
}

PLATFORM_TYPE_MAP: dict[str, str] = {
    "社媒传播类": "social_media", "垂类社区类": "vertical_community",
    "垂类官方媒体类": "vertical_official", "电商平台": "ecommerce",
    "搜索引擎": "search_engine",
    "竞品官方电商": "competitor_dtc", "第三方评测类": "third_party_review",
}

DEFAULT_SEGMENT_BY_LINE: dict[str, tuple[str, str, str]] = {
    "吸奶器": ("SEG01", "产后建奶新手妈妈", "产后0-6月"),
    "喂养电器": ("SEG02", "精细喂养效率型妈妈", "0-12月"),
    "家居出行": ("SEG03", "出行场景育儿家庭", "孕晚期-24月"),
    "内衣服饰": ("SEG04", "孕产护理妈妈", "孕期-产后6月"),
    "护理电器": ("SEG05", "清洁护理妈妈", "0-12月"),
    "母婴综合护理": ("SEG06", "综合护理家庭", "孕期-24月"),
    "智能母婴电器": ("SEG07", "智能育儿家庭", "0-24月"),
    "家居家纺": ("SEG08", "家居布品家庭", "孕期-24月"),
}

PRIORITY_VALID = {"P0", "P1", "P2", "P3"}

BRAND_NORMALIZE_MAP: dict[str, str] = {
    "willow": "Willow", "medela": "Medela", "spectra": "Spectra",
    "elvie": "Elvie", "lansinoh": "Lansinoh", "momcozy": "Momcozy",
    "eufy": "Eufy", "bebefun": "Bebefun", "baby buddha": "Baby Buddha",
    "bellababy": "BellaBaby", "lacteck": "Lacteck", "mumma bump": "Mumma Bump",
    "ameda": "Ameda", "motif medical": "Motif Medical", "evenflo": "Evenflo",
}

PAIN_SUBCATEGORY_RULES: dict[str, list[tuple[list[str], str]]] = {
    "吸奶器": [
        (["suction", "吸力", "letdown", "output", "pump.*slow", "not.*enough.*milk"], "吸力不足/衰减"),
        (["app", "bluetooth", "connect", "wifi", "sync", "APP", "连接"], "APP/连接问题"),
        (["battery", "charge", "续航", "电量", "power.*off", "dead.*battery"], "续航/电量问题"),
        (["noise", "loud", "motor", "噪音", "noisy", "sound"], "电机/噪音问题"),
        (["leak", "spill", "seal", "泄漏", "漏奶", "overflow", "drip"], "泄漏/密封问题"),
        (["size", "fit", "flange", "尺寸", "尺码", "不合", "cup.*size", "shield"], "尺寸/适配问题"),
        (["comfort", "pain", "hurt", "sore", "nipple", "舒适", "疼", "uncomfortable"], "佩戴舒适度"),
        (["portable", "heavy", "weight", "bulk", "便携", "重", "大"], "便携性/重量"),
        (["clean", "wash", "hygiene", "mold", "清洁", "维护", "saniti"], "清洁/维护困难"),
        (["price", "expensive", "cost", "worth", "贵", "价格", "性价比", "afford"], "整体性价比低"),
        (["accessory", "part", "replacement", "配件", "耗材", "spare"], "配件/耗材价格高"),
        (["refund", "return", "退款", "退货", "money.*back"], "退款/售后困难"),
        (["customer.*service", "support", "response", "客服", "售后", "reply"], "客服响应差"),
        (["shipping", "delivery", "deliver", "发货", "配送", "延迟", "late"], "发货延迟"),
        (["out.*of.*stock", "unavailable", "backorder", "缺货", "断货"], "配件断货"),
        (["smell", "material", "plastic", "bpa", "材质", "气味", "odor"], "材质/气味问题"),
        (["broke", "broken", "crack", "defect", "quality", "损坏", "坏了", "故障", "malfunction"], "产品损坏/质量缺陷"),
    ],
    "喂养电器": [
        (["overheat", "too hot", "overheating", "burn", "fire", "smoke", "过热", "着火", "冒烟", "überhitzt", "surchauffe"], "过热/安全隐患"),
        (["plastic.*smell", "chemical", "toxic", "bpa", "off-gas", "塑料味", "异味", "化学", "Plastikgeruch", "odeur.*plastique"], "材质/气味问题"),
        (["not.*warm", "won't.*heat", "no.*heat", "temperature", "inconsistent.*heat", "不加热", "温度不均", "不热"], "加热功能失效"),
        (["broke", "broken", "stopped.*working", "dead", "malfunction", "kaputt", "defekt", "cassé", "roto", "停止", "故障"], "产品损坏/停止运转"),
        (["hard.*clean", "mold", "build.*up", "residue", "calcium", "descal", "难以清洗", "发霉", "结垢", "水垢"], "清洗困难/卫生问题"),
        (["leak", "spill", "water.*leak", "漏水", "泄漏"], "漏水/密封问题"),
        (["loud", "noise", "noisy", "vibrat", "噪音", "声音大", "laut", "bruit"], "噪音/震动问题"),
        (["price", "expensive", "overpriced", "not.*worth", "贵", "性价比", "不值", "teuer", "cher", "caro"], "整体性价比低"),
        (["refund", "return", "warranty", "customer.*service", "退款", "退货", "售后", "客服", "Kundendienst"], "售后/退款困难"),
        (["shipping", "delivery", "delay", "发货", "配送", "延迟", "Lieferung", "livraison"], "发货延迟"),
        (["formula", "powder", "inconsistent.*amount", "dispensing", "配方奶", "奶粉", "冲泡"], "配方/冲泡问题"),
        (["rust", "corros", "peel", "coat", "Rost", "rouille", "óxido", "生锈", "涂层"], "锈蚀/涂层脱落"),
    ],
}

PAIN_SUBCATEGORY_PARENT: dict[str, str] = {
    # 吸奶器
    "吸力不足/衰减": "功能", "APP/连接问题": "功能", "续航/电量问题": "功能", "电机/噪音问题": "功能",
    "泄漏/密封问题": "体验", "尺寸/适配问题": "体验", "佩戴舒适度": "体验", "便携性/重量": "体验", "清洁/维护困难": "体验",
    "整体性价比低": "价格", "配件/耗材价格高": "价格",
    "退款/售后困难": "服务", "客服响应差": "服务", "发货延迟": "服务", "配件断货": "服务",
    "材质/气味问题": "安全", "产品损坏/质量缺陷": "安全",
    # 喂养电器
    "过热/安全隐患": "安全", "加热功能失效": "功能", "产品损坏/停止运转": "功能",
    "清洗困难/卫生问题": "体验", "漏水/密封问题": "体验", "噪音/震动问题": "体验",
    "售后/退款困难": "服务", "配方/冲泡问题": "功能", "锈蚀/涂层脱落": "安全",
}


def normalize_brand(v: str | None) -> str | None:
    if not v:
        return None
    s = clean_str(v) or ""
    return BRAND_NORMALIZE_MAP.get(s.lower(), s)


def infer_pain_subcategory(product_line: str, text: str, theme: str = "") -> str:
    """Infer pain_subcategory from product_line-specific keyword rules."""
    rules = PAIN_SUBCATEGORY_RULES.get(product_line, [])
    combined = (text + " " + theme).lower()
    for keywords, subcategory in rules:
        for kw in keywords:
            if re.search(kw, combined, re.IGNORECASE):
                return subcategory
    return "其他"


def is_chinese_text(text: str | None) -> bool:
    """Check if text has >= 30% Chinese characters."""
    if not text:
        return False
    chinese_chars = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return len(text) > 0 and (chinese_chars / len(text)) >= 0.3


# ── 清洗工具函数 ──

def clean_str(v) -> str | None:
    """去除空白、不间断空格、HTML 实体残留。"""
    if v is None:
        return None
    s = str(v).strip().replace("\u00a0", " ")
    s = re.sub(r"&nbsp;?", " ", s)
    s = s.replace("&amp;", "&")
    return s if s else None


def clean_num(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("¥", "").replace("$", "").replace("€", "")
    try:
        return float(s)
    except ValueError:
        return None


def clean_int(v) -> int | None:
    n = clean_num(v)
    return int(n) if n is not None else None


def normalize_separator(v: str | None) -> str | None:
    """统一多值分隔符为英文逗号。"""
    if not v:
        return None
    return ", ".join(
        seg.strip() for seg in re.split(r"[、/；;｜|\n]", v) if seg.strip()
    )


def get_code(name: str | None) -> str | None:
    if not name:
        return None
    cleaned = clean_str(name)
    code = COUNTRY_CODE_MAP.get(cleaned)
    if code is None and cleaned:
        print(f"  WARN: no ISO code for country: '{cleaned}'")
    return code


def normalize_product_line(v: str | None) -> str:
    if not v:
        return "unknown"
    s = clean_str(v) or ""
    return PRODUCT_LINE_MAP.get(s, s)


def normalize_priority(v: str | None) -> str:
    s = (clean_str(v) or "").upper()
    return s if s in PRIORITY_VALID else "P3"


def normalize_platform_type(v: str | None) -> str:
    s = clean_str(v) or ""
    return PLATFORM_TYPE_MAP.get(s, "other")


def get_default_segment(product_line: str | None) -> tuple[str, str, str]:
    return DEFAULT_SEGMENT_BY_LINE.get(product_line or "", ("SEG99", "综合育儿用户", "孕期-24月"))


def infer_platform_type_from_name(platform: str | None) -> str:
    p = (clean_str(platform) or "").lower()
    if not p:
        return "other"
    if any(x in p for x in ["reddit", "mumsnet", "netmums", "babycenter", "whattoexpect", "urbia", "forum"]):
        return "vertical_community"
    if any(x in p for x in ["trustpilot", "babygearlab", "wirecutter", "review"]):
        return "third_party_review"
    if any(x in p for x in ["instagram", "facebook", "tiktok", "youtube", "x.com", "twitter"]):
        return "social_media"
    if any(x in p for x in ["shopify", "momcozy", "official", "官网", "独立站"]):
        return "competitor_dtc"
    if any(x in p for x in ["amazon", "walmart", "ebay", "tmall", "jd", "shopee", "noon", "bestbuy"]):
        return "ecommerce"
    return "other"


# ── CSV 读取 ──

def read_csv_table(filepath: Path) -> list[dict]:
    """读取 CSV 文件，返回字典列表。跳过首列为空的行。"""
    if not filepath.exists():
        print(f"  WARN: {filepath.name} not found, returning empty list")
        return []
    result = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            first_key = next(iter(row)) if row else None
            if first_key and not (row.get(first_key) or "").strip():
                continue
            result.append(row)
    return result
