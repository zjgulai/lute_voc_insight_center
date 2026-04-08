# -*- coding: utf-8 -*-
"""清洗 dim_country_product_persona.csv → personas section。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, get_code, normalize_product_line,
    normalize_separator, TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_country_product_persona.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        result.append({
            "country": country,
            "country_code": get_code(country),
            "product_line": normalize_product_line(r.get("产品品线")),
            "identity_profile": clean_str(r.get("身份画像")),
            "media_preference": clean_str(r.get("媒体偏好")),
            "purchase_habit": clean_str(r.get("购买习惯")),
            "brand_preference": clean_str(r.get("品牌偏好")),
            "competitor_brands": clean_str(r.get("核心竞争品牌（国际/本土）")),
            "competitor_models": clean_str(r.get("核心竞品产品名称/型号")),
            "marketing_preference": clean_str(r.get("营销偏好")),
            "social_platforms": normalize_separator(clean_str(r.get("社媒传播类平台"))),
            "vertical_communities": normalize_separator(clean_str(r.get("垂类社区平台"))),
            "vertical_media": normalize_separator(clean_str(r.get("垂类官方媒体平台"))),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
