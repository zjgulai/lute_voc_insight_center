# -*- coding: utf-8 -*-
"""
export_viz_json.py — 读取 data/delivery/tables/ 下的CSV文件，
通过 tools/cleaning/ 各清洗模块处理后输出：
  - data/delivery/viz_country_insight.json  (国家洞察看板)
  - data/delivery/viz_opportunity.json      (机会点挖掘看板)
  - data/delivery/viz_dataset.json          (merged 兼容)

用法:
    python tools/export_viz_json.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ))

from tools.cleaning._common import DELIVERY_DIR, TABLES_DIR
from tools.cleaning import (
    clean_dim_project_meta,
    clean_dim_country_product_persona,
    clean_dim_top20_country_insight,
    clean_dim_cluster_strategy,
    clean_dim_country_price_sensitivity,
    clean_dim_info_source_quality,
    clean_cfg_top10_platform_entry,
    clean_cfg_top10_country_line,
    clean_cfg_p1_search_playbook,
    clean_dim_country_segment_matrix,
    clean_voc_summary_flat,
    clean_voc_summary_persona_flat,
    clean_dim_voc_negative_extract,
)

OUTPUT_COUNTRY = DELIVERY_DIR / "viz_country_insight.json"
OUTPUT_OPPORTUNITY = DELIVERY_DIR / "viz_opportunity.json"
OUTPUT_MERGED = DELIVERY_DIR / "viz_dataset.json"

CSV_SOURCE_FILES = [
    "dim_project_meta.csv",
    "dim_country_product_persona.csv",
    "dim_top20_country_insight.csv",
    "dim_cluster_strategy.csv",
    "dim_country_price_sensitivity.csv",
    "dim_info_source_quality.csv",
    "cfg_top10_platform_entry.csv",
    "cfg_top10_country_line.csv",
    "cfg_p1_search_playbook.csv",
    "dim_country_segment_matrix.csv",
    "voc_summary_flat.csv",
    "voc_summary_persona_flat.csv",
    "dim_voc_negative_extract.csv",
]


def build_countries(personas, top20, keywords) -> list[dict]:
    top20_set = {r["country_code"] for r in top20 if r.get("country_code")}
    top10_set = {r["country_code"] for r in keywords if r.get("country_code")}
    seen: set[str] = set()
    countries = []
    for p in personas:
        code = p.get("country_code")
        name = p.get("country")
        if not code or code in seen:
            continue
        seen.add(code)
        sales = None
        for t in top20:
            if t.get("country_code") == code:
                sales = t.get("sales_amount")
                break
        countries.append({
            "code": code,
            "name_cn": name,
            "is_top20": code in top20_set,
            "is_top10": code in top10_set,
            "sales_amount": sales,
        })
    return sorted(countries, key=lambda c: c.get("sales_amount") or 0, reverse=True)


def build_voc_timeline(voc_negative: list[dict]) -> list[dict]:
    """Aggregate voc_negative by period/country/product_line/brand/pain_category."""
    agg: dict[str, dict] = {}
    for r in voc_negative:
        date = r.get("collect_date", "")[:10] or "unknown"
        country = r.get("country", "")
        product_line = r.get("product_line", "")
        brand = r.get("competitor_brand", "") or "unknown"
        pain = r.get("pain_category", "")
        batch = r.get("batch_code", "")
        key = f"{date}|{country}|{product_line}|{brand}|{pain}"
        if key not in agg:
            agg[key] = {
                "period": date,
                "batch_code": batch,
                "country": country,
                "product_line": product_line,
                "competitor_brand": brand,
                "pain_category": pain,
                "count": 0,
                "frequency": 0,
                "high_intensity_count": 0,
            }
        agg[key]["count"] += 1
        agg[key]["frequency"] += r.get("frequency", 0) or 0
        if r.get("intensity") == "高":
            agg[key]["high_intensity_count"] += 1
    return sorted(agg.values(), key=lambda x: (x["period"], x["country"]))


def build_competitor_ingest_meta(voc_negative: list[dict]) -> dict:
    """Build metadata about competitor ingest batches."""
    comp_rows = [r for r in voc_negative if (r.get("batch_code") or "").startswith("COMP-")]
    if not comp_rows:
        return {"has_competitor_data": False}
    brand_dist: dict[str, int] = {}
    for r in comp_rows:
        b = r.get("competitor_brand", "unknown")
        brand_dist[b] = brand_dist.get(b, 0) + 1
    batches = sorted(set(r.get("batch_code", "") for r in comp_rows))
    return {
        "has_competitor_data": True,
        "total_competitor_rows": len(comp_rows),
        "brand_distribution": dict(sorted(brand_dist.items(), key=lambda x: -x[1])),
        "batches": batches,
    }


def main():
    print("Building sections from CSV files...")

    overview = clean_dim_project_meta.build()
    print(f"  overview: {len(overview)} rows")

    personas = clean_dim_country_product_persona.build()
    print(f"  personas: {len(personas)} rows")

    top20 = clean_dim_top20_country_insight.build()
    print(f"  top20: {len(top20)} rows")

    clusters = clean_dim_cluster_strategy.build()
    print(f"  clusters: {len(clusters)} rows")

    purchasing_power = clean_dim_country_price_sensitivity.build()
    print(f"  purchasing_power: {len(purchasing_power)} rows")

    trust_sources = clean_dim_info_source_quality.build()
    print(f"  trust_sources: {len(trust_sources)} rows")

    platforms = clean_cfg_top10_platform_entry.build()
    print(f"  platforms: {len(platforms)} rows")

    keywords = clean_cfg_top10_country_line.build()
    print(f"  keywords: {len(keywords)} rows")

    p1_search = clean_cfg_p1_search_playbook.build()
    print(f"  p1_search: {len(p1_search)} rows")

    segments = clean_dim_country_segment_matrix.build()
    print(f"  segments: {len(segments)} rows")

    voc_summary = clean_voc_summary_flat.build()
    print(f"  voc_summary: {len(voc_summary)} rows")

    voc_persona_summary = clean_voc_summary_persona_flat.build()
    print(f"  voc_persona_summary: {len(voc_persona_summary)} rows")

    voc_negative = clean_dim_voc_negative_extract.build()
    print(f"  voc_negative: {len(voc_negative)} rows")

    countries = build_countries(personas, top20, keywords)
    print(f"  countries: {len(countries)} rows")

    voc_timeline = build_voc_timeline(voc_negative)
    print(f"  voc_timeline: {len(voc_timeline)} rows")

    competitor_meta = build_competitor_ingest_meta(voc_negative)
    print(f"  competitor_ingest: {'yes' if competitor_meta['has_competitor_data'] else 'no'}")

    now = datetime.now(timezone.utc).isoformat()
    base_meta = {
        "generated_at": now,
        "source_files": CSV_SOURCE_FILES,
        "total_countries": len(countries),
        "total_product_lines": len({p["product_line"] for p in personas}),
    }

    country_insight = {
        "meta": {**base_meta, "dashboard": "country_insight"},
        "overview": overview,
        "countries": countries,
        "personas": personas,
        "top20": top20,
        "clusters": clusters,
        "purchasing_power": purchasing_power,
        "segments": segments,
        "keywords": keywords,
        "platforms": platforms,
        "voc_summary": voc_summary,
    }

    opportunity = {
        "meta": {**base_meta, "dashboard": "opportunity"},
        "platforms": platforms,
        "trust_sources": trust_sources,
        "voc_summary": voc_summary,
        "voc_persona_summary": voc_persona_summary,
        "voc_negative": voc_negative,
        "p1_search": p1_search,
        "voc_timeline": voc_timeline,
        "competitor_ingest_meta": competitor_meta,
    }

    merged = {
        "meta": base_meta,
        "overview": overview,
        "countries": countries,
        "personas": personas,
        "top20": top20,
        "clusters": clusters,
        "purchasing_power": purchasing_power,
        "trust_sources": trust_sources,
        "platforms": platforms,
        "keywords": keywords,
        "p1_search": p1_search,
        "segments": segments,
        "voc_summary": voc_summary,
        "voc_persona_summary": voc_persona_summary,
        "voc_negative": voc_negative,
        "voc_timeline": voc_timeline,
        "competitor_ingest_meta": competitor_meta,
    }

    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    for path, data, label in [
        (OUTPUT_COUNTRY, country_insight, "country_insight"),
        (OUTPUT_OPPORTUNITY, opportunity, "opportunity"),
        (OUTPUT_MERGED, merged, "merged"),
    ]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        recs = sum(len(v) for v in data.values() if isinstance(v, list))
        print(f"  -> {path.name}: {recs} records")

    print(f"\nCountries: {len(countries)}")
    null_codes = [c for c in countries if not c.get("code")]
    if null_codes:
        print(f"\nWARN: {len(null_codes)} countries without ISO code")

    from tools.validate_viz_dataset import run_checks
    _passed, _failed = run_checks(merged)

    if _failed > 0:
        print(f"WARN: {_failed} validation check(s) failed — review output above")
    else:
        print("All validation checks passed.")

    print("\nDone.")


if __name__ == "__main__":
    main()
