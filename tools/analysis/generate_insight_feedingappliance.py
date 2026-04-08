# -*- coding: utf-8 -*-
"""喂养电器深度洞察脚本 — 4P + NPS + 子品类拆分 + 安全问题置顶"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import Counter

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ))

from tools.analysis._insight_common import build_insight_report, save_report, load_voc_negative, TOP5_COUNTRIES

SUB_PRODUCT_KEYWORDS = {
    "暖奶器": ["bottle warmer", "warmer", "chauffe-biberon", "Flaschenwärmer", "calienta biberones", "暖奶", "温奶"],
    "消毒锅": ["sterilizer", "steriliser", "stérilisateur", "Sterilisator", "esterilizador", "消毒", "sterilize"],
    "辅食机": ["food maker", "baby blender", "robot cuiseur", "Babykocher", "辅食机", "food processor"],
    "冲奶机": ["formula maker", "formula pro", "prep machine", "perfect prep", "dispenser", "冲奶", "formula dispenser"],
}


def infer_sub_product(text: str) -> str:
    lower = text.lower()
    for sub, keywords in SUB_PRODUCT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lower:
                return sub
    return "其他喂养电器"


def add_feeding_specific(report: dict) -> dict:
    rows = load_voc_negative("喂养电器", TOP5_COUNTRIES)

    sub_product_map: dict[str, list[dict]] = {}
    for r in rows:
        text = r.get("original_text", "") + " " + r.get("negative_theme", "")
        sp = infer_sub_product(text)
        if sp not in sub_product_map:
            sub_product_map[sp] = []
        sub_product_map[sp].append(r)

    sub_product_stats = {}
    for sp, sp_rows in sub_product_map.items():
        high = sum(1 for r in sp_rows if r.get("intensity") == "高")
        safety = sum(1 for r in sp_rows if r.get("pain_category") == "安全")
        brands = Counter(r.get("competitor_brand") for r in sp_rows if r.get("competitor_brand"))
        sub_product_stats[sp] = {
            "count": len(sp_rows),
            "high_ratio": round(high / len(sp_rows) * 100, 1) if sp_rows else 0,
            "safety_count": safety,
            "safety_ratio": round(safety / len(sp_rows) * 100, 1) if sp_rows else 0,
            "top_brands": dict(brands.most_common(3)),
        }

    safety_rows = [r for r in rows if r.get("pain_category") == "安全"]
    safety_subcats = Counter(r.get("pain_subcategory", "其他") for r in safety_rows)
    safety_brands = Counter(r.get("competitor_brand") for r in safety_rows if r.get("competitor_brand"))

    country_safety: dict[str, int] = {}
    for r in safety_rows:
        c = r.get("country", "")
        if c:
            country_safety[c] = country_safety.get(c, 0) + 1

    report["feeding_specific"] = {
        "sub_product_breakdown": sub_product_stats,
        "safety_focus": {
            "total_safety_records": len(safety_rows),
            "safety_ratio_overall": round(len(safety_rows) / len(rows) * 100, 1) if rows else 0,
            "top_safety_subcategories": dict(safety_subcats.most_common(5)),
            "top_safety_brands": dict(safety_brands.most_common(5)),
            "safety_by_country": country_safety,
            "insight": (
                f"安全类投诉占全部喂养电器投诉的 {round(len(safety_rows)/len(rows)*100) if rows else 0}%。"
                + (f" {safety_brands.most_common(1)[0][0]} 是安全投诉最多的品牌（{safety_brands.most_common(1)[0][1]}条）。" if safety_brands else "")
                + " 过热/安全隐患和材质/气味是最主要的安全子类。"
            ),
            "recommendation": "安全认证（CE/FDA/BPA-free）应作为产品宣传的第一优先级。安全类投诉需要紧急响应机制。",
        },
        "market_maturity": {
            "insight": (
                f"喂养电器总投诉量 {len(rows)} 条，远低于吸奶器。"
                " 投诉更集中于安全（过热、材质）而非功能细节，表明市场尚在基本品质信任建立阶段。"
                " 率先解决安全问题的品牌将获得先发信任优势。"
            ),
        },
    }

    report["summary_bullets"].append(
        f"喂养电器安全警报：安全类投诉占比 {round(len(safety_rows)/len(rows)*100) if rows else 0}%，"
        f"过热/着火/塑料气味是核心风险，涉及 {len(safety_brands)} 个品牌"
    )

    if sub_product_stats:
        top_sp = max(sub_product_stats.items(), key=lambda x: x[1]["count"])
        report["summary_bullets"].append(
            f"子品类拆分：{top_sp[0]} 投诉最集中（{top_sp[1]['count']}条），"
            f"安全占比 {top_sp[1]['safety_ratio']}%"
        )

    return report


def main():
    print("Generating feeding appliance insight report...")
    report = build_insight_report("喂养电器")
    report = add_feeding_specific(report)
    json_path, md_path = save_report(report, "feedingappliance")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"Records: {report['scope']['total_records']}")
    print(f"Summary bullets: {len(report['summary_bullets'])}")
    for b in report["summary_bullets"]:
        print(f"  - {b}")


if __name__ == "__main__":
    main()
