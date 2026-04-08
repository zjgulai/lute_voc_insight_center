# -*- coding: utf-8 -*-
"""清洗 dim_top20_country_insight.csv → top20 section。"""
from __future__ import annotations
from ._common import read_csv_table, clean_str, clean_num, get_code, TABLES_DIR


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_top20_country_insight.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        result.append({
            "country": country,
            "country_code": get_code(country),
            "sales_amount": clean_num(r.get("销售额")),
            "insight": clean_str(r.get("国家洞察")),
            "top_negative_themes": clean_str(r.get("主要负面主题")),
            "negative_volume": clean_str(r.get("负面声量估算")),
            "competitor_pain_points": clean_str(r.get("竞品痛点")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
