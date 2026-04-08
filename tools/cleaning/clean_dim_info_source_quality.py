# -*- coding: utf-8 -*-
"""清洗 dim_info_source_quality.csv → trust_sources section。

字段映射变化（相比原xlsx）：
- 原 `来源名称` / `链接` → CSV中为 `代表平台` / `代表入口`
- CSV新增：适配客群、建议用途、关键词方向、来源获取方式、风险说明
"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, get_code,
    normalize_product_line, normalize_priority, TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_info_source_quality.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        result.append({
            "country": country,
            "country_code": get_code(country),
            "region_cluster": clean_str(r.get("区域cluster")),
            "product_line": normalize_product_line(r.get("产品品线")),
            "competitor_brands": clean_str(r.get("核心竞争品牌（国际/本土）")),
            "competitor_models": clean_str(r.get("核心竞品产品名称/型号")),
            "priority": normalize_priority(r.get("品线优先级")),
            "sample_segment": clean_str(r.get("样本客群")),
            "research_question_type": clean_str(r.get("研究问题类型")),
            "source_tier": clean_str(r.get("来源层级")),
            "source_type": clean_str(r.get("来源类型")),
            "source_name": clean_str(r.get("代表平台")),
            "entry": clean_str(r.get("代表入口")),
            "target_segment": clean_str(r.get("适配客群")),
            "suggested_usage": clean_str(r.get("建议用途")),
            "keyword_direction": clean_str(r.get("关键词方向")),
            "access_method": clean_str(r.get("来源获取方式")),
            "risk_notes": clean_str(r.get("风险说明")),
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
