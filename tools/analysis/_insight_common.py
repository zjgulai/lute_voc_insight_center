# -*- coding: utf-8 -*-
"""
共用数据加载、4P 框架映射、NPS 代理计算、品牌竞争力矩阵。
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ))

from tools.cleaning._common import PAIN_SUBCATEGORY_PARENT

VIZ_OPP = PROJ / "data" / "delivery" / "viz_opportunity.json"
PROCESSED_DIR = PROJ / "data" / "processed"
REPORTS_DIR = PROJ / "reports"

TOP5_COUNTRIES = ["美国", "加拿大", "英国", "德国", "法国"]

FOUR_P_MAP = {
    "Product": ["功能", "安全"],
    "Price": ["价格"],
    "Place": ["服务"],
    "Promotion": ["体验"],
}


def load_voc_negative(product_line: str | None = None, countries: list[str] | None = None) -> list[dict]:
    with open(VIZ_OPP, "r", encoding="utf-8") as f:
        ds = json.load(f)
    rows = ds.get("voc_negative", [])
    if product_line:
        rows = [r for r in rows if r.get("product_line") == product_line]
    if countries:
        rows = [r for r in rows if r.get("country") in countries]
    return rows


def compute_4p(rows: list[dict]) -> dict[str, Any]:
    result = {}
    for p_label, pain_cats in FOUR_P_MAP.items():
        p_rows = [r for r in rows if r.get("pain_category") in pain_cats]
        total = len(p_rows)
        high = sum(1 for r in p_rows if r.get("intensity") == "高")
        freq = sum(r.get("frequency", 1) or 1 for r in p_rows)

        subcat_counter = Counter(r.get("pain_subcategory", "其他") for r in p_rows)
        top_subcats = [{"name": k, "count": v} for k, v in subcat_counter.most_common(5) if k != "其他"]

        brand_counter = Counter(r.get("competitor_brand") for r in p_rows if r.get("competitor_brand"))
        top_brands = [{"name": k, "count": v} for k, v in brand_counter.most_common(5)]

        high_ratio = round(high / total * 100, 1) if total > 0 else 0

        brand_quality = {}
        for brand, _ in brand_counter.most_common(10):
            b_rows = [r for r in p_rows if r.get("competitor_brand") == brand]
            b_high = sum(1 for r in b_rows if r.get("intensity") == "高")
            brand_quality[brand] = round((1 - b_high / len(b_rows)) * 100, 1) if b_rows else 100

        insight_parts = []
        if top_subcats:
            insight_parts.append(f"TOP 子分类：{top_subcats[0]['name']}（{top_subcats[0]['count']}条）")
        if top_brands:
            insight_parts.append(f"最多被提及品牌：{top_brands[0]['name']}（{top_brands[0]['count']}条）")
        insight_parts.append(f"高强度占比 {high_ratio}%")

        recommendations = {
            "Product": f"优先解决 {top_subcats[0]['name'] if top_subcats else '核心功能缺陷'}，降低高强度比（当前 {high_ratio}%）",
            "Price": f"{'价格敏感主要来自 ' + top_brands[0]['name'] if top_brands else '整体性价比'} 用户群，建议差异化定价",
            "Place": f"渠道服务痛点集中于 {top_subcats[0]['name'] if top_subcats else '售后'}，建议加强本地化售后",
            "Promotion": f"体验类投诉高强度比 {high_ratio}%，宣传时避免过度承诺使用便利性",
        }

        result[p_label] = {
            "total_records": total,
            "frequency_sum": freq,
            "high_intensity_count": high,
            "high_intensity_ratio": high_ratio,
            "top_subcategories": top_subcats,
            "top_brands": top_brands,
            "brand_quality_score": brand_quality,
            "insight": " | ".join(insight_parts),
            "recommendation": recommendations.get(p_label, ""),
        }
    return result


def compute_nps_proxy(rows: list[dict], dimension: str = "brand") -> dict[str, Any]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        key = r.get("competitor_brand") if dimension == "brand" else r.get("country")
        if key:
            groups[key].append(r)

    scores = {}
    for key, g_rows in groups.items():
        cat_map: dict[str, list[dict]] = defaultdict(list)
        for r in g_rows:
            cat_map[r.get("pain_category", "体验")].append(r)

        def dim_score(cat: str) -> float:
            cr = cat_map.get(cat, [])
            if not cr:
                return 100.0
            high = sum(1 for r in cr if r.get("intensity") == "高")
            return round((1 - high / len(cr)) * 100, 1)

        func_s = dim_score("功能")
        exp_s = dim_score("体验")
        price_s = 100.0 - round(len(cat_map.get("价格", [])) / max(len(g_rows), 1) * 100, 1)
        svc_s = dim_score("服务")
        composite = round(func_s * 0.4 + exp_s * 0.3 + price_s * 0.15 + svc_s * 0.15, 1)

        scores[key] = {
            "composite": composite,
            "functional": func_s,
            "experience": exp_s,
            "price_perception": price_s,
            "service": svc_s,
            "record_count": len(g_rows),
        }

    detractors = [r for r in rows if r.get("intensity") == "高"]
    det_counter = Counter(r.get("pain_subcategory", "其他") for r in detractors)
    det_drivers = [f"{k}（{v}条高强度）" for k, v in det_counter.most_common(5) if k != "其他"]

    passives = [r for r in rows if r.get("intensity") == "中"]
    pas_counter = Counter(r.get("pain_subcategory", "其他") for r in passives)
    pas_drivers = [f"{k}（{v}条中等）" for k, v in pas_counter.most_common(5) if k != "其他"]

    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["composite"])
    worst = sorted_scores[0] if sorted_scores else None
    best = sorted_scores[-1] if sorted_scores else None

    insight = f"NPS 代理得分范围 {worst[1]['composite'] if worst else '—'} ~ {best[1]['composite'] if best else '—'}。"
    if worst:
        insight += f" {worst[0]} 综合分最低（{worst[1]['composite']}），主要拖累维度为功能（{worst[1]['functional']}）。"

    return {
        f"by_{dimension}": {k: v["composite"] for k, v in scores.items()},
        "detail": scores,
        "detractors_drivers": det_drivers,
        "passives_drivers": pas_drivers,
        "insight": insight,
        "recommendation": f"优先改善 {det_drivers[0] if det_drivers else '高强度痛点'}，可挽回 {len(passives)} 条中等不满用户",
    }


def compute_country_comparison(rows: list[dict]) -> dict[str, Any]:
    country_pain: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    country_brand: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        c = r.get("country", "")
        pc = r.get("pain_category", "")
        brand = r.get("competitor_brand", "")
        if c and pc:
            country_pain[c][pc] += r.get("frequency", 1) or 1
        if c and brand:
            country_brand[c][brand] += 1

    pain_heatmap = []
    for c, pains in sorted(country_pain.items()):
        for p, v in pains.items():
            pain_heatmap.append({"country": c, "pain_category": p, "frequency": v})

    brand_dominance = {c: dict(counter.most_common(3)) for c, counter in country_brand.items()}

    return {
        "pain_heatmap": pain_heatmap,
        "brand_dominance_by_country": brand_dominance,
        "insight": f"覆盖 {len(country_pain)} 个国家，各国痛点分布存在差异",
    }


def compute_competitive_intelligence(rows: list[dict]) -> dict[str, Any]:
    brands = set(r.get("competitor_brand") for r in rows if r.get("competitor_brand"))
    matrix = {}
    for brand in sorted(brands):
        b_rows = [r for r in rows if r.get("competitor_brand") == brand]
        cat_dist = Counter(r.get("pain_category") for r in b_rows)
        total = len(b_rows)
        high = sum(1 for r in b_rows if r.get("intensity") == "高")

        def level(cat: str) -> str:
            cnt = cat_dist.get(cat, 0)
            ratio = cnt / total if total > 0 else 0
            if ratio > 0.3:
                return "极高"
            elif ratio > 0.15:
                return "高"
            elif ratio > 0.05:
                return "中"
            return "低"

        matrix[brand] = {
            "total": total,
            "high_ratio": round(high / total * 100, 1) if total > 0 else 0,
            "功能": level("功能"),
            "体验": level("体验"),
            "价格": level("价格"),
            "服务": level("服务"),
            "安全": level("安全"),
        }

    weakest = max(matrix.items(), key=lambda x: x[1]["high_ratio"]) if matrix else None
    opportunities = []
    if weakest:
        opportunities.append(f"{weakest[0]} 高强度比最高（{weakest[1]['high_ratio']}%），可作为差异化突破口")

    return {
        "brand_vulnerability_matrix": matrix,
        "whitespace_opportunities": opportunities,
        "insight": f"共识别 {len(brands)} 个竞品品牌的脆弱性分布",
    }


def generate_summary_bullets(rows: list[dict], product_line: str, four_p: dict, nps: dict, comp: dict) -> list[str]:
    bullets = []
    total = len(rows)
    high = sum(1 for r in rows if r.get("intensity") == "高")
    countries = set(r.get("country") for r in rows if r.get("country"))
    brands = set(r.get("competitor_brand") for r in rows if r.get("competitor_brand"))

    bullets.append(f"本次分析覆盖 {len(countries)} 个国家、{len(brands)} 个竞品品牌、{total} 条负面记录，高强度占比 {round(high/total*100) if total else 0}%")

    prod = four_p.get("Product", {})
    if prod.get("top_subcategories"):
        top = prod["top_subcategories"][0]
        bullets.append(f"Product 维度：{top['name']} 是最突出的产品缺陷（{top['count']}条），高强度比 {prod['high_intensity_ratio']}%")

    nps_brands = nps.get("by_brand", {})
    if nps_brands:
        worst_brand = min(nps_brands.items(), key=lambda x: x[1])
        bullets.append(f"NPS 代理：{worst_brand[0]} 综合分最低（{worst_brand[1]}分），是主要竞品薄弱品牌")

    if nps.get("detractors_drivers"):
        bullets.append(f"强烈不满用户（Detractors）核心驱动因素：{nps['detractors_drivers'][0]}")

    ci = comp.get("brand_vulnerability_matrix", {})
    if ci:
        high_vuln = [(k, v) for k, v in ci.items() if v.get("high_ratio", 0) > 30]
        if high_vuln:
            bullets.append(f"竞争情报：{', '.join(h[0] for h in high_vuln[:3])} 的高强度投诉比超过 30%，为我方差异化突破窗口")

    return bullets


def build_insight_report(product_line: str, countries: list[str] | None = None) -> dict:
    scope_countries = countries or TOP5_COUNTRIES
    rows = load_voc_negative(product_line, scope_countries)

    four_p = compute_4p(rows)
    nps_brand = compute_nps_proxy(rows, "brand")
    nps_country = compute_nps_proxy(rows, "country")
    country_comp = compute_country_comparison(rows)
    competitive = compute_competitive_intelligence(rows)
    bullets = generate_summary_bullets(rows, product_line, four_p, nps_brand, competitive)

    return {
        "product_line": product_line,
        "scope": {"countries": scope_countries, "total_records": len(rows)},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "framework_4p": four_p,
        "nps_proxy": {
            "by_brand": nps_brand.get("by_brand", {}),
            "by_country": nps_country.get("by_country", {}),
            "brand_detail": nps_brand.get("detail", {}),
            "country_detail": nps_country.get("detail", {}),
            "detractors_drivers": nps_brand.get("detractors_drivers", []),
            "passives_drivers": nps_brand.get("passives_drivers", []),
            "insight": nps_brand.get("insight", ""),
            "recommendation": nps_brand.get("recommendation", ""),
        },
        "country_comparison": country_comp,
        "competitive_intelligence": competitive,
        "summary_bullets": bullets,
    }


def save_report(report: dict, product_line: str) -> tuple[Path, Path]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = PROCESSED_DIR / f"insight_{product_line}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    md_path = REPORTS_DIR / f"insight_{product_line}.md"
    lines = [f"# {product_line} 深度洞察报告", ""]
    lines.append(f"**生成时间**: {report['generated_at']}")
    lines.append(f"**覆盖范围**: {', '.join(report['scope']['countries'])}，共 {report['scope']['total_records']} 条记录")
    lines.append("")

    lines.append("## 核心结论")
    for b in report.get("summary_bullets", []):
        lines.append(f"- {b}")
    lines.append("")

    lines.append("## 4P 营销框架分析")
    for p_label, p_data in report.get("framework_4p", {}).items():
        lines.append(f"\n### {p_label}")
        lines.append(f"- 记录数: {p_data['total_records']}，频次: {p_data['frequency_sum']}，高强度: {p_data['high_intensity_count']}（{p_data['high_intensity_ratio']}%）")
        lines.append(f"- 洞察: {p_data['insight']}")
        lines.append(f"- 建议: {p_data['recommendation']}")

    lines.append("\n## NPS 代理分析")
    nps = report.get("nps_proxy", {})
    lines.append(f"- 洞察: {nps.get('insight', '')}")
    lines.append(f"- 建议: {nps.get('recommendation', '')}")
    if nps.get("by_brand"):
        lines.append("\n### 品牌 NPS 代理得分")
        for brand, score in sorted(nps["by_brand"].items(), key=lambda x: x[1]):
            lines.append(f"  - {brand}: {score}")

    lines.append("\n## 竞争情报")
    ci = report.get("competitive_intelligence", {})
    lines.append(f"- {ci.get('insight', '')}")
    for opp in ci.get("whitespace_opportunities", []):
        lines.append(f"- 机会: {opp}")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return json_path, md_path
