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
from collections import Counter
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
OUTPUT_OPPORTUNITY_INTERNAL = DELIVERY_DIR / "viz_opportunity_internal.json"
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

INTERNAL_BATCH_PREFIX = "MOMCOZY-"


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


def split_voc_negative(voc_negative: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split VOC rows into public(competitor/external) and internal datasets by batch prefix."""
    internal_rows: list[dict] = []
    public_rows: list[dict] = []
    for r in voc_negative:
        batch = (r.get("batch_code") or "")
        if batch.startswith(INTERNAL_BATCH_PREFIX):
            internal_rows.append(r)
        else:
            public_rows.append(r)
    return public_rows, internal_rows


def build_internal_voc_summary(voc_negative: list[dict]) -> list[dict]:
    """Build internal voc_summary rows directly from internal voc_negative records."""
    agg: dict[tuple[str, str], dict] = {}
    for r in voc_negative:
        country = r.get("country", "")
        product_line = r.get("product_line", "")
        key = (country, product_line)
        if key not in agg:
            agg[key] = {
                "country": country,
                "country_code": r.get("country_code"),
                "cluster": r.get("cluster", ""),
                "product_line": product_line,
                "total_comments": 0,
                "row_count": 0,
                "pain_counter": Counter(),
                "high_intensity_count": 0,
                "persona_coverage": set(),
                "platform_coverage": set(),
                "theme_counter": Counter(),
                "brand_counter": Counter(),
                "summary_date": "",
            }
        item = agg[key]
        weight = r.get("frequency", 0) or 1
        item["total_comments"] += weight
        item["row_count"] += 1
        pain = r.get("pain_category", "") or "其他"
        item["pain_counter"][pain] += weight
        if r.get("intensity") == "高":
            item["high_intensity_count"] += weight
        if r.get("segment_code"):
            item["persona_coverage"].add(r["segment_code"])
        if r.get("platform"):
            item["platform_coverage"].add(r["platform"])
        if r.get("negative_theme"):
            item["theme_counter"][r["negative_theme"]] += weight
        if r.get("competitor_brand"):
            item["brand_counter"][r["competitor_brand"]] += weight
        collect_date = r.get("collect_date", "") or ""
        if collect_date and collect_date > item["summary_date"]:
            item["summary_date"] = collect_date

    def pct(counter: Counter, key: str, total: int) -> float:
        if total <= 0:
            return 0.0
        return round(counter.get(key, 0) / total * 100, 1)

    result = []
    for item in agg.values():
        total = item["total_comments"]
        result.append({
            "country": item["country"],
            "country_code": item["country_code"],
            "cluster": item["cluster"],
            "product_line": item["product_line"],
            "total_comments": total,
            "top5_negative_themes": ";".join(
                name for name, _ in item["theme_counter"].most_common(5)
            ),
            "pain_function_pct": pct(item["pain_counter"], "功能", total),
            "pain_price_pct": pct(item["pain_counter"], "价格", total),
            "pain_experience_pct": pct(item["pain_counter"], "体验", total),
            "pain_service_pct": pct(item["pain_counter"], "服务", total),
            "pain_safety_pct": pct(item["pain_counter"], "安全", total),
            "high_intensity_pct": round(item["high_intensity_count"] / total * 100, 1) if total > 0 else 0,
            "persona_coverage_cnt": len(item["persona_coverage"]),
            "platform_coverage_cnt": len(item["platform_coverage"]),
            "top_competitor_brands": ";".join(
                name for name, _ in item["brand_counter"].most_common(3)
            ),
            "summary_date": item["summary_date"],
        })
    return sorted(result, key=lambda x: (x["country"], x["product_line"]))


def build_internal_voc_persona_summary(voc_negative: list[dict]) -> list[dict]:
    """Build internal voc_persona_summary rows directly from internal voc_negative records."""
    agg: dict[tuple[str, str, str, str], dict] = {}
    for r in voc_negative:
        country = r.get("country", "")
        product_line = r.get("product_line", "")
        platform = r.get("platform", "")
        segment_code = r.get("segment_code", "")
        key = (country, product_line, platform, segment_code)
        if key not in agg:
            agg[key] = {
                "country": country,
                "country_code": r.get("country_code"),
                "cluster": r.get("cluster", ""),
                "product_line": product_line,
                "platform_type": r.get("platform_type", "other"),
                "platform": platform,
                "segment_code": segment_code,
                "segment_name": r.get("segment_name", ""),
                "lifecycle": r.get("lifecycle", ""),
                "content_cnt": 0,
                "total_comments": 0,
                "theme_counter": Counter(),
                "brand_counter": Counter(),
                "collect_start": "",
                "collect_end": "",
                "batch_codes": set(),
            }
        item = agg[key]
        weight = r.get("frequency", 0) or 1
        item["content_cnt"] += 1
        item["total_comments"] += weight
        if r.get("negative_theme"):
            item["theme_counter"][r["negative_theme"]] += weight
        if r.get("competitor_brand"):
            item["brand_counter"][r["competitor_brand"]] += weight
        collect_date = r.get("collect_date", "") or ""
        if collect_date and (not item["collect_start"] or collect_date < item["collect_start"]):
            item["collect_start"] = collect_date
        if collect_date and collect_date > item["collect_end"]:
            item["collect_end"] = collect_date
        if r.get("batch_code"):
            item["batch_codes"].add(r["batch_code"])

    result = []
    for item in agg.values():
        total = item["total_comments"]
        result.append({
            "country": item["country"],
            "country_code": item["country_code"],
            "cluster": item["cluster"],
            "product_line": item["product_line"],
            "platform_type": item["platform_type"],
            "platform": item["platform"],
            "segment_code": item["segment_code"],
            "segment_name": item["segment_name"],
            "lifecycle": item["lifecycle"],
            "content_cnt": item["content_cnt"],
            "valid_comment_cnt": total,
            "total_comments": total,
            "positive_cnt": 0,
            "negative_cnt": total,
            "neutral_cnt": 0,
            "negative_rate": 100 if total > 0 else 0,
            "top3_negative": ";".join(
                name for name, _ in item["theme_counter"].most_common(3)
            ),
            "top3_positive": "",
            "top3_competitors": ";".join(
                name for name, _ in item["brand_counter"].most_common(3)
            ),
            "collect_start": item["collect_start"],
            "collect_end": item["collect_end"],
            "batch_code": ";".join(sorted(item["batch_codes"])),
            "data_quality": "B",
        })
    return sorted(
        result,
        key=lambda x: (x["country"], x["product_line"], x["platform"], x["segment_code"]),
    )


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

    public_voc_negative, internal_voc_negative = split_voc_negative(voc_negative)
    print(f"  voc_negative_public: {len(public_voc_negative)} rows")
    print(f"  voc_negative_internal: {len(internal_voc_negative)} rows")

    voc_timeline = build_voc_timeline(public_voc_negative)
    print(f"  voc_timeline_public: {len(voc_timeline)} rows")
    voc_timeline_internal = build_voc_timeline(internal_voc_negative)
    print(f"  voc_timeline_internal: {len(voc_timeline_internal)} rows")

    competitor_meta = build_competitor_ingest_meta(public_voc_negative)
    print(f"  competitor_ingest: {'yes' if competitor_meta['has_competitor_data'] else 'no'}")

    internal_brand_dist: dict[str, int] = {}
    for r in internal_voc_negative:
        b = r.get("competitor_brand", "unknown")
        internal_brand_dist[b] = internal_brand_dist.get(b, 0) + 1
    internal_meta = {
        "has_internal_data": len(internal_voc_negative) > 0,
        "total_internal_rows": len(internal_voc_negative),
        "total_internal_frequency": sum((r.get("frequency", 0) or 0) for r in internal_voc_negative),
        "brand_distribution": dict(sorted(internal_brand_dist.items(), key=lambda x: -x[1])),
        "batches": sorted(set((r.get("batch_code") or "") for r in internal_voc_negative if r.get("batch_code"))),
    }
    internal_voc_summary = build_internal_voc_summary(internal_voc_negative)
    print(f"  voc_summary_internal: {len(internal_voc_summary)} rows")
    internal_voc_persona_summary = build_internal_voc_persona_summary(internal_voc_negative)
    print(f"  voc_persona_summary_internal: {len(internal_voc_persona_summary)} rows")

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
        "voc_negative": public_voc_negative,
        "p1_search": p1_search,
        "voc_timeline": voc_timeline,
        "competitor_ingest_meta": competitor_meta,
    }

    opportunity_internal = {
        "meta": {**base_meta, "dashboard": "opportunity_internal"},
        "platforms": platforms,
        "trust_sources": trust_sources,
        "voc_summary": internal_voc_summary,
        "voc_persona_summary": internal_voc_persona_summary,
        "voc_negative": internal_voc_negative,
        "p1_search": p1_search,
        "voc_timeline": voc_timeline_internal,
        "internal_ingest_meta": internal_meta,
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
        "voc_timeline": build_voc_timeline(voc_negative),
        "competitor_ingest_meta": competitor_meta,
    }

    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    for path, data, label in [
        (OUTPUT_COUNTRY, country_insight, "country_insight"),
        (OUTPUT_OPPORTUNITY, opportunity, "opportunity"),
        (OUTPUT_OPPORTUNITY_INTERNAL, opportunity_internal, "opportunity_internal"),
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
