# -*- coding: utf-8 -*-
"""清洗 cfg_top10_country_line.csv → keywords section（含核心关键词字段）。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, clean_num, clean_int, get_code,
    normalize_product_line, normalize_priority, normalize_separator,
    TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "cfg_top10_country_line.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        result.append({
            "country": country,
            "country_code": get_code(country),
            "product_line": normalize_product_line(r.get("产品品线")),
            "competitor_brands": clean_str(r.get("核心竞争品牌（国际/本土）")),
            "competitor_models": clean_str(r.get("核心竞品产品名称/型号")),
            "sales_amount": clean_num(r.get("销售额")),
            "country_total_sales": clean_num(r.get("国家总销售额")),
            "share_in_country": clean_str(r.get("国家内占比")),
            "line_rank": clean_int(r.get("品线排名")),
            "crawl_priority": normalize_priority(r.get("抓取优先级")),
            "priority_note": clean_str(r.get("优先级说明")),
            "core_product_terms": normalize_separator(clean_str(r.get("核心产品词"))),
            "pain_point_terms": normalize_separator(clean_str(r.get("痛点词"))),
            "scenario_terms": normalize_separator(clean_str(r.get("场景词"))),
            "decision_terms": normalize_separator(clean_str(r.get("决策词"))),
            "topic_clusters": clean_str(r.get("主题簇")),
            "recommended_entry": clean_str(r.get("推荐入口")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
