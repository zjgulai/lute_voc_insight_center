# -*- coding: utf-8 -*-
"""清洗 dim_country_price_sensitivity.csv → purchasing_power section（含扩展字段）。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, clean_num, get_code,
    normalize_product_line, normalize_priority, TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_country_price_sensitivity.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        result.append({
            "country": country,
            "country_code": get_code(country),
            "region_cluster": clean_str(r.get("区域cluster")),
            "purchasing_power_tier": clean_str(r.get("国家购买力层级")),
            "product_line": normalize_product_line(r.get("产品品线")),
            "competitor_brands": clean_str(r.get("核心竞争品牌（国际/本土）")),
            "competitor_models": clean_str(r.get("核心竞品产品名称/型号")),
            "priority": normalize_priority(r.get("品线优先级")),
            "sample_segment": clean_str(r.get("样本客群")),
            "spending_mindset": clean_str(r.get("品类支出心智")),
            "price_sensitivity": clean_str(r.get("价格敏感方式")),
            # CSV 扩展字段
            "bundle_preference": clean_str(r.get("套装偏好")),
            "gift_preference": clean_str(r.get("赠品偏好")),
            "promo_sensitivity": clean_str(r.get("节点促销敏感度")),
            "brand_tier_preference": clean_str(r.get("品牌梯度偏好")),
            "purchase_channel_preference": clean_str(r.get("成交偏好渠道")),
            "recommended_price_strategy": clean_str(r.get("推荐价格策略")),
            "recommended_promo_tactic": clean_str(r.get("推荐促销打法")),
            "recommended_bundle_direction": clean_str(r.get("推荐套装方向")),
            "recommended_gift_direction": clean_str(r.get("推荐赠品方向")),
            "risk_notes": clean_str(r.get("主要风险提示")),
            "local_judgment": clean_str(r.get("国家本地判断")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:2], ensure_ascii=False, indent=2))
