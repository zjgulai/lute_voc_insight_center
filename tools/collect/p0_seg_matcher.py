"""
P0 采集脚本 3/4 — SEG 画像批量匹配器

功能：
  读取 dim_voc_negative_extract.csv，对尚未标注画像的行自动匹配 SEG 编码，
  并输出匹配质量报告。

使用场景：
  - 半自动采集后统一跑画像匹配
  - P3 阶段的画像校准预处理

输出：
  - 更新 dim_voc_negative_extract.csv 中空白画像编码
  - 打印匹配质量统计
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"

SEG_RULES = {
    "SEG01": {
        "name": "产后建奶新手妈妈",
        "lifecycle": "产后0-3月",
        "keywords_en": [
            "newborn", "first time", "ftm", "new mom", "new mum",
            "postpartum", "just had", "week old", "month old baby",
            "learning to pump", "first pump",
        ],
        "keywords_local": {
            "DE": ["erstgebärende", "neugeborenes", "frisch entbunden", "wochenbett"],
            "FR": ["primipare", "nouveau-né", "post-partum", "première fois"],
            "ES": ["primeriza", "recién nacido", "posparto", "primera vez"],
            "AR": ["حديثة الولادة", "أول مرة", "مولود جديد"],
        },
        "weight": 1.0,
    },
    "SEG02": {
        "name": "返岗背奶效率妈妈",
        "lifecycle": "产后3-12月",
        "keywords_en": [
            "work", "office", "commute", "back to work", "workplace",
            "coworker", "lunch break", "pumping room", "desk", "meeting",
            "quiet", "portable for work", "hands free at work",
        ],
        "keywords_local": {
            "DE": ["arbeit", "büro", "pendeln", "zurück zur arbeit", "kollegin"],
            "FR": ["travail", "bureau", "retour au travail", "collègue", "trajet"],
            "ES": ["trabajo", "oficina", "regreso al trabajo", "compañera"],
            "AR": ["عمل", "مكتب", "العودة للعمل"],
        },
        "weight": 1.2,
    },
    "SEG03": {
        "name": "高频泵奶复购家庭",
        "lifecycle": "产后0-12月",
        "keywords_en": [
            "replace", "replacement", "second", "bought again", "reorder",
            "wore out", "used daily", "months of use", "heavy use",
            "cost of parts", "refill", "consumable",
        ],
        "keywords_local": {
            "DE": ["ersatz", "ersatzteil", "nachkaufen", "täglicher gebrauch", "verschleiß"],
            "FR": ["remplacement", "remplacer", "usure", "quotidien", "pièces"],
            "ES": ["reemplazo", "repuesto", "desgaste", "uso diario", "segunda vez"],
            "AR": ["استبدال", "قطع غيار", "استخدام يومي"],
        },
        "weight": 1.0,
    },
}


def detect_language_hint(country: str) -> str:
    """从国家名称推断本地化关键词语言组"""
    lang_map = {
        "德国": "DE", "奥地利": "DE",
        "法国": "FR", "比利时": "FR",
        "西班牙": "ES", "墨西哥": "ES",
        "阿联酋": "AR", "沙特阿拉伯": "AR",
    }
    return lang_map.get(country, "")


def score_segment(text: str, seg_code: str, country: str = "") -> float:
    """计算文本与指定 SEG 的匹配分数"""
    rule = SEG_RULES[seg_code]
    lower = text.lower()
    score = 0.0

    for kw in rule["keywords_en"]:
        if kw.lower() in lower:
            score += 1.0

    lang = detect_language_hint(country)
    if lang and lang in rule["keywords_local"]:
        for kw in rule["keywords_local"][lang]:
            if kw.lower() in lower:
                score += 1.5

    return score * rule["weight"]


def match_segment(text: str, country: str = "") -> tuple[str, float, dict[str, float]]:
    """返回 (最佳 SEG 编码, 最高分, 各 SEG 分数)"""
    scores = {}
    for seg in SEG_RULES:
        scores[seg] = score_segment(text, seg, country)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "SEG01"
        scores["SEG01"] = 0.1

    return best, scores[best], scores


def process_csv():
    """读取 CSV，对空画像编码行进行匹配"""
    if not TARGET_CSV.exists():
        print(f"[错误] 目标文件不存在: {TARGET_CSV}")
        return

    rows = []
    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    seg_counter = Counter()
    confidence_stats = {"高置信": 0, "中置信": 0, "低置信": 0}

    for row in rows:
        combined = f"{row.get('负面原文摘录(本地语言)', '')} {row.get('负面原文摘录(中文翻译)', '')} {row.get('负面主题', '')}"
        country = row.get("国家", "")

        current_seg = row.get("画像编码", "").strip()

        best_seg, best_score, all_scores = match_segment(combined, country)
        seg_counter[best_seg] += 1

        if best_score >= 3.0:
            confidence_stats["高置信"] += 1
        elif best_score >= 1.0:
            confidence_stats["中置信"] += 1
        else:
            confidence_stats["低置信"] += 1

        if not current_seg or current_seg == "":
            row["画像编码"] = best_seg
            row["画像名称"] = SEG_RULES[best_seg]["name"]
            row["生命周期"] = SEG_RULES[best_seg]["lifecycle"]
            updated += 1

    with open(TARGET_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("=" * 60)
    print(f"[SEG 匹配器] 处理完成")
    print(f"  总行数: {len(rows)}")
    print(f"  更新画像: {updated} 行")
    print(f"\n  画像分布:")
    for seg, count in sorted(seg_counter.items()):
        pct = count / len(rows) * 100 if rows else 0
        print(f"    {seg} ({SEG_RULES[seg]['name']}): {count} 条 ({pct:.1f}%)")
    print(f"\n  匹配置信度:")
    for level, count in confidence_stats.items():
        pct = count / len(rows) * 100 if rows else 0
        print(f"    {level}: {count} 条 ({pct:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    process_csv()
