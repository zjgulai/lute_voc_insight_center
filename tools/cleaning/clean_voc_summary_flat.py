# -*- coding: utf-8 -*-
"""清洗 voc_summary_flat.csv → voc_summary section。

适配 tables/ 版真实列名：
  国家, 区域cluster, 产品品线, 负面主题TOP5, 总条目数,
  功能占比, 价格占比, 体验占比, 服务占比, 安全占比,
  高强度占比, 涉及画像数, 涉及平台数, 竞品品牌TOP3, 汇总日期
"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, clean_int, get_code,
    normalize_product_line, TABLES_DIR,
)


def _pct(raw: str | None) -> float:
    """Parse a percentage string like '50%' or '0%' into 0–100 float."""
    if not raw:
        return 0.0
    raw = raw.strip().replace("%", "").replace("％", "")
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "voc_summary_flat.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        total = clean_int(r.get("总条目数")) or 0

        pain_function = _pct(r.get("功能占比"))
        pain_price = _pct(r.get("价格占比"))
        pain_experience = _pct(r.get("体验占比"))
        pain_service = _pct(r.get("服务占比"))
        pain_safety = _pct(r.get("安全占比"))
        high_intensity = _pct(r.get("高强度占比"))

        result.append({
            "country": country,
            "country_code": get_code(country),
            "cluster": clean_str(r.get("区域cluster")),
            "product_line": normalize_product_line(r.get("产品品线")),
            "total_comments": total,
            "top5_negative_themes": clean_str(r.get("负面主题TOP5")),
            "pain_function_pct": pain_function,
            "pain_price_pct": pain_price,
            "pain_experience_pct": pain_experience,
            "pain_service_pct": pain_service,
            "pain_safety_pct": pain_safety,
            "high_intensity_pct": high_intensity,
            "persona_coverage_cnt": clean_int(r.get("涉及画像数")) or 0,
            "platform_coverage_cnt": clean_int(r.get("涉及平台数")) or 0,
            "top_competitor_brands": clean_str(r.get("竞品品牌TOP3")),
            "summary_date": clean_str(r.get("汇总日期")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
