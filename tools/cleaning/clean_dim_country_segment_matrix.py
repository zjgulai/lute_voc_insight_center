# -*- coding: utf-8 -*-
"""清洗 dim_country_segment_matrix.csv → segments section（新增）。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, get_code,
    normalize_product_line, normalize_priority, normalize_separator,
    TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_country_segment_matrix.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        result.append({
            "country": country,
            "country_code": get_code(country),
            "region_cluster": clean_str(r.get("区域cluster")),
            "purchasing_power_initial": clean_str(r.get("国家购买力初判")),
            "product_line": normalize_product_line(r.get("产品品线")),
            "competitor_brands": clean_str(r.get("核心竞争品牌（国际/本土）")),
            "competitor_models": clean_str(r.get("核心竞品产品名称/型号")),
            "priority": normalize_priority(r.get("品线优先级")),
            "segment_code": clean_str(r.get("客群编码")),
            "segment_name": clean_str(r.get("客群名称")),
            "lifecycle": clean_str(r.get("生命周期")),
            "family_structure": clean_str(r.get("家庭结构")),
            "decision_driver": clean_str(r.get("决策驱动")),
            "core_pain_points": clean_str(r.get("核心痛点")),
            "key_purchase_motivation": clean_str(r.get("关键购买动机")),
            "main_resistance": clean_str(r.get("主要阻力")),
            "core_trust_source": clean_str(r.get("核心信任来源")),
            "priority_content_angle": clean_str(r.get("优先内容切口")),
            "price_sensitivity_initial": clean_str(r.get("价格敏感初判")),
            "local_marketing_angle": clean_str(r.get("本地化营销切口")),
            "social_platforms": normalize_separator(clean_str(r.get("社媒传播类平台"))),
            "community_platforms": normalize_separator(clean_str(r.get("垂类社区平台"))),
            "official_media_platforms": normalize_separator(clean_str(r.get("垂类官方媒体平台"))),
            "local_judgment": clean_str(r.get("国家本地判断")),
            "source_index": clean_str(r.get("来源索引")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
