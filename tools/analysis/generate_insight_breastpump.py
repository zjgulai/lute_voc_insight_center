# -*- coding: utf-8 -*-
"""吸奶器深度洞察脚本 — 4P + NPS + 穿戴式/插电式对比"""
from __future__ import annotations
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ))

from tools.analysis._insight_common import build_insight_report, save_report, load_voc_negative, load_internal_voc_negative, TOP5_COUNTRIES
from collections import Counter

WEARABLE_BRANDS = {"Elvie", "Willow", "Momcozy", "Baby Buddha", "BellaBaby"}
PLUG_IN_BRANDS = {"Medela", "Spectra", "Lansinoh", "Ameda", "Motif Medical", "Evenflo"}


def add_breastpump_specific(report: dict) -> dict:
    loader = load_internal_voc_negative if report.get("source") == "internal" else load_voc_negative
    rows = loader("吸奶器", TOP5_COUNTRIES)

    wearable = [r for r in rows if r.get("competitor_brand") in WEARABLE_BRANDS]
    plugin = [r for r in rows if r.get("competitor_brand") in PLUG_IN_BRANDS]

    def pain_dist(subset: list[dict]) -> dict[str, int]:
        c = Counter(r.get("pain_subcategory", "其他") for r in subset)
        return dict(c.most_common(8))

    def high_ratio(subset: list[dict]) -> float:
        if not subset:
            return 0.0
        return round(sum(1 for r in subset if r.get("intensity") == "高") / len(subset) * 100, 1)

    report["breastpump_specific"] = {
        "wearable_vs_plugin": {
            "wearable": {
                "count": len(wearable),
                "high_ratio": high_ratio(wearable),
                "top_pain_subcategories": pain_dist(wearable),
                "brands": list(WEARABLE_BRANDS & set(r.get("competitor_brand") for r in wearable)),
            },
            "plugin": {
                "count": len(plugin),
                "high_ratio": high_ratio(plugin),
                "top_pain_subcategories": pain_dist(plugin),
                "brands": list(PLUG_IN_BRANDS & set(r.get("competitor_brand") for r in plugin)),
            },
            "insight": (
                f"穿戴式泵 {len(wearable)} 条投诉（高强度 {high_ratio(wearable)}%），"
                f"插电式泵 {len(plugin)} 条（高强度 {high_ratio(plugin)}%）。"
                + (" 穿戴式高强度比更高，主要集中在泄漏和连接问题。" if high_ratio(wearable) > high_ratio(plugin) else " 插电式高强度比更高，主要集中在吸力和噪音问题。")
            ),
        },
    }

    co_occur: dict[str, int] = {}
    for r in rows:
        sc = r.get("pain_subcategory", "")
        theme = r.get("negative_theme", "")
        if sc and theme and sc != theme and sc != "其他":
            pair = tuple(sorted([sc, theme]))
            key = f"{pair[0]} + {pair[1]}"
            co_occur[key] = co_occur.get(key, 0) + 1
    top_combos = sorted(co_occur.items(), key=lambda x: -x[1])[:5]
    report["breastpump_specific"]["pain_co_occurrence"] = [
        {"combination": k, "count": v} for k, v in top_combos
    ]

    promo_insight = []
    for brand in WEARABLE_BRANDS:
        b_rows = [r for r in rows if r.get("competitor_brand") == brand]
        if not b_rows:
            continue
        exp_rows = [r for r in b_rows if r.get("pain_category") == "体验"]
        if exp_rows:
            ratio = round(len(exp_rows) / len(b_rows) * 100)
            promo_insight.append(f"{brand}: 体验类占 {ratio}% — 宣传'便携自由'但实际泄漏/适配问题多")
    report["breastpump_specific"]["promotion_gap"] = promo_insight

    report["summary_bullets"].append(
        f"穿戴式 vs 插电式：穿戴式投诉 {len(wearable)} 条（高强度 {high_ratio(wearable)}%），"
        f"插电式 {len(plugin)} 条（{high_ratio(plugin)}%）"
    )

    return report


def main():
    print("Generating breast pump insight report...")
    for source in ("public", "internal"):
        report = build_insight_report("吸奶器", source=source)
        report = add_breastpump_specific(report)
        json_path, md_path = save_report(report, "breastpump", source=source)
        print(f"[{source}] JSON: {json_path}")
        print(f"[{source}] Markdown: {md_path}")
        print(f"[{source}] Records: {report['scope']['total_records']}")
        print(f"[{source}] Summary bullets: {len(report['summary_bullets'])}")
        for b in report["summary_bullets"]:
            print(f"  - {b}")


if __name__ == "__main__":
    main()
