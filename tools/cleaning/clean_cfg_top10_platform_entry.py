# -*- coding: utf-8 -*-
"""清洗 cfg_top10_platform_entry.csv → platforms section。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, clean_num, get_code,
    normalize_product_line, normalize_platform_type, TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "cfg_top10_platform_entry.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        result.append({
            "country": country,
            "country_code": get_code(country),
            "country_sales": clean_num(r.get("国家销售额")),
            "priority_line": clean_str(r.get("优先品线")),
            "competitor_brands": clean_str(r.get("核心竞争品牌（国际/本土）")),
            "competitor_models": clean_str(r.get("核心竞品产品名称/型号")),
            "country_judgment": clean_str(r.get("国家判断")),
            "platform_type": normalize_platform_type(r.get("平台类型")),
            "platform": clean_str(r.get("平台")),
            "entry_section": clean_str(r.get("入口/版块")),
            "access_method": clean_str(r.get("访问方式")),
            "keyword_pack": clean_str(r.get("关键词包")),
            "sampling_advice": clean_str(r.get("采样建议")),
            "source_index": clean_str(r.get("来源索引")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
