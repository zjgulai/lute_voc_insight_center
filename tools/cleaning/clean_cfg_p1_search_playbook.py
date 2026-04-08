# -*- coding: utf-8 -*-
"""清洗 cfg_p1_search_playbook.csv → p1_search section（新增）。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, clean_num, get_code,
    normalize_product_line, normalize_priority, normalize_separator,
    TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "cfg_p1_search_playbook.csv")
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
            "line_rank": clean_str(r.get("品线排名")),
            "crawl_priority": normalize_priority(r.get("抓取优先级")),
            "priority_note": clean_str(r.get("优先级说明")),
            "core_product_terms": normalize_separator(clean_str(r.get("核心产品词"))),
            "pain_point_terms": normalize_separator(clean_str(r.get("痛点词"))),
            "scenario_terms": normalize_separator(clean_str(r.get("场景词"))),
            "decision_terms": normalize_separator(clean_str(r.get("决策词"))),
            "topic_clusters": clean_str(r.get("主题簇")),
            "recommended_entry": clean_str(r.get("推荐入口")),
            "site_search_query": clean_str(r.get("站内搜索语句")),
            "community_boolean_query": clean_str(r.get("社区布尔组合")),
            "decision_search_query": clean_str(r.get("决策搜索组合")),
            "local_language_variant": clean_str(r.get("本地语言变体")),
            "google_search_query": clean_str(r.get("推荐Google搜索")),
            "mixed_test_terms": clean_str(r.get("中英混合测试词")),
            "entry_1": clean_str(r.get("入口1")),
            "entry_2": clean_str(r.get("入口2")),
            "entry_3": clean_str(r.get("入口3")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:2], ensure_ascii=False, indent=2))
