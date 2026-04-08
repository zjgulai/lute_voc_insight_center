# -*- coding: utf-8 -*-
"""清洗 dim_cluster_strategy.csv → clusters section。"""
from __future__ import annotations
from ._common import read_csv_table, clean_str, clean_int, TABLES_DIR


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_cluster_strategy.csv")
    result = []
    for r in rows:
        cluster = clean_str(r.get("区域cluster"))
        if not cluster:
            continue
        result.append({
            "cluster": cluster,
            "representative_countries": clean_str(r.get("TOP20代表国家")),
            "top20_count": clean_int(r.get("TOP20国家数")),
            "common_customer_traits": clean_str(r.get("共性客群特征")),
            "common_trust_sources": clean_str(r.get("共性信任来源")),
            "common_content_angle": clean_str(r.get("共性内容切口")),
            "common_price_strategy": clean_str(r.get("共性价格策略")),
            "channel_focus": clean_str(r.get("渠道与平台侧重")),
            "country_differences": clean_str(r.get("国家差异点")),
            "recommended_actions": clean_str(r.get("建议优先动作")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
