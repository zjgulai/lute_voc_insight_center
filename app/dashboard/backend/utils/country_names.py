"""Bidirectional country name mapping (ISO ↔ Chinese) for VOC countries."""
from __future__ import annotations

ISO_TO_CN: dict[str, str] = {
    "US": "美国", "UK": "英国", "GB": "英国", "DE": "德国", "FR": "法国",
    "JP": "日本", "AU": "澳大利亚", "CA": "加拿大", "IT": "意大利",
    "ES": "西班牙", "KR": "韩国", "IN": "印度", "BR": "巴西",
    "MX": "墨西哥", "SA": "沙特阿拉伯", "AE": "阿联酋", "TH": "泰国",
    "ID": "印尼", "MY": "马来西亚", "SG": "新加坡", "PH": "菲律宾",
    "VN": "越南", "PL": "波兰", "NL": "荷兰", "SE": "瑞典",
    "NO": "挪威", "DK": "丹麦", "FI": "芬兰", "TR": "土耳其",
    "RU": "俄罗斯", "ZA": "南非", "EG": "埃及", "NG": "尼日利亚",
    "KE": "肯尼亚", "AR": "阿根廷", "CL": "智利", "CO": "哥伦比亚",
    "PE": "秘鲁", "CN": "中国", "TW": "中国台湾", "HK": "中国香港",
    "NZ": "新西兰", "IE": "爱尔兰", "AT": "奥地利", "CH": "瑞士",
    "BE": "比利时", "PT": "葡萄牙", "CZ": "捷克", "RO": "罗马尼亚",
    "HU": "匈牙利", "GR": "希腊", "IL": "以色列", "PK": "巴基斯坦",
    "BD": "孟加拉", "LK": "斯里兰卡", "OM": "阿曼", "LB": "黎巴嫩",
    "AL": "阿尔巴尼亚", "BG": "保加利亚", "GT": "危地马拉",
    "HR": "克罗地亚", "KH": "柬埔寨", "KW": "科威特", "LT": "立陶宛",
    "TN": "突尼斯", "UZ": "乌兹别克斯坦", "XK": "科索沃",
}

CN_TO_ISO: dict[str, str] = {}
for _k, _v in ISO_TO_CN.items():
    if _v not in CN_TO_ISO:
        CN_TO_ISO[_v] = _k

# Handle alternate Chinese names found in raw data
_CN_ALIASES: dict[str, str] = {"印度尼西亚": "ID", "沙特": "SA"}
for _alias, _code in _CN_ALIASES.items():
    CN_TO_ISO[_alias] = _code


def normalize_country(value: str | None, target: str = "cn") -> str | None:
    """Convert a country identifier to the desired format.

    Args:
        value: ISO code (e.g. "US") or Chinese name (e.g. "美国"), or None.
        target: "cn" to return Chinese name, "iso" to return ISO code.

    Returns:
        Converted value, or the original value if no mapping exists, or None.
    """
    if not value:
        return None
    v = value.strip()
    if not v:
        return None

    upper = v.upper()
    if target == "cn":
        if upper in ISO_TO_CN:
            return ISO_TO_CN[upper]
        if v in CN_TO_ISO:
            return v
        return v
    else:  # target == "iso"
        if v in CN_TO_ISO:
            return CN_TO_ISO[v]
        if upper in ISO_TO_CN:
            return upper
        return v
