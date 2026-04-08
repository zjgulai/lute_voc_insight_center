"""
P3 脚本 — 画像匹配 + 质量打分 + 审核标记

功能：
  1. 批量重跑 SEG 画像匹配（增强版，支持多字段交叉打分）
  2. 数据质量打分（0-100），逐行标注质量等级
  3. 竞品品牌标准化（对齐 competitor_registry 中的品牌名）
  4. 标记需人工审核的行（低置信/缺字段/异常值）
  5. 输出审核工作单 CSV（供人工 review）

输出：
  更新 dim_voc_negative_extract.csv 原地
  tools/collect/output/p3_review_queue.csv（需人工审核行）
  tools/collect/output/p3_quality_report.txt
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import date
from pathlib import Path

from competitor_registry import COMPETITOR_BRANDS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
OUTPUT_DIR = Path(__file__).parent / "output"

VALID_PAIN = {"功能", "价格", "体验", "服务", "安全"}
VALID_INTENSITY = {"高", "中", "低"}
VALID_SEG = {"SEG01", "SEG02", "SEG03"}

ALL_BRAND_NAMES = set()
BRAND_ALIAS_MAP: dict[str, str] = {}
for b in COMPETITOR_BRANDS:
    canonical = b["brand"]
    ALL_BRAND_NAMES.add(canonical)
    BRAND_ALIAS_MAP[canonical.lower()] = canonical
    for model in b.get("key_models", []):
        prefix = model.split()[0]
        BRAND_ALIAS_MAP[prefix.lower()] = canonical
    BRAND_ALIAS_MAP[canonical.lower().replace(" ", "")] = canonical
    BRAND_ALIAS_MAP[canonical.lower().replace(".", "")] = canonical


# ── 增强版 SEG 匹配 ──

SEG_RULES = {
    "SEG01": {
        "name": "产后建奶新手妈妈",
        "lifecycle": "产后0-3月",
        "keywords": [
            "newborn", "first time", "ftm", "new mom", "new mum", "postpartum",
            "just had", "week old", "learning", "first pump", "breastfeeding journey",
            "新手", "第一次", "刚生", "产后",
            "primipare", "nouveau-né", "erstgebärende", "neugeborenes",
            "primeriza", "recién nacido", "حديثة الولادة", "أول مرة",
        ],
        "weight": 1.0,
    },
    "SEG02": {
        "name": "返岗背奶效率妈妈",
        "lifecycle": "产后3-12月",
        "keywords": [
            "work", "office", "commute", "back to work", "workplace", "desk",
            "meeting", "lunch break", "pumping room", "hands free at work",
            "上班", "返岗", "办公室", "工作",
            "travail", "bureau", "arbeit", "büro", "trabajo", "oficina",
            "عمل", "مكتب",
        ],
        "weight": 1.2,
    },
    "SEG03": {
        "name": "高频泵奶复购家庭",
        "lifecycle": "产后0-12月",
        "keywords": [
            "replace", "replacement", "second", "again", "reorder", "wore out",
            "daily", "heavy use", "months of use", "cost of parts", "refill",
            "复购", "二胎", "换", "消耗",
            "remplacement", "ersatz", "reemplazo", "استبدال",
        ],
        "weight": 1.0,
    },
}


def match_seg(text: str) -> tuple[str, float]:
    lower = text.lower()
    scores = {}
    for seg, rule in SEG_RULES.items():
        score = sum(1.0 for kw in rule["keywords"] if kw.lower() in lower)
        scores[seg] = score * rule["weight"]
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "SEG01", 0.0
    return best, scores[best]


def guess_pain(text: str) -> str:
    lower = text.lower()
    rules = [
        ("安全", ["safe", "safety", "bpa", "toxic", "smell", "chemical", "sicher", "sécur", "segur", "مادة"]),
        ("价格", ["price", "expensive", "cost", "money", "cheap", "refund", "prix", "preis", "precio", "cher"]),
        ("服务", ["service", "support", "warranty", "return", "customer", "售后", "garantie", "servicio"]),
        ("功能", ["suction", "power", "motor", "battery", "broken", "defect", "pump", "saugleistung", "aspiration", "succión", "شفط"]),
        ("体验", ["pain", "noise", "loud", "uncomfortable", "flange", "size", "clean", "leak", "douleur", "schmerz", "dolor", "ألم"]),
    ]
    for cat, keywords in rules:
        if any(kw in lower for kw in keywords):
            return cat
    return "体验"


def guess_intensity(text: str) -> str:
    lower = text.lower()
    high = ["terrible", "worst", "useless", "dangerous", "horrible", "waste",
            "never again", "furchtbar", "inutile", "peligroso", "أسوأ"]
    low = ["minor", "slightly", "okay", "ok", "fine", "acceptable", "légèrement", "etwas"]
    if any(w in lower for w in high):
        return "高"
    if any(w in lower for w in low):
        return "低"
    return "中"


def normalize_competitors(raw: str) -> str:
    if not raw:
        return ""
    parts = re.split(r"[;,，；\s]+", raw.strip())
    normalized = set()
    for p in parts:
        p = p.strip()
        if not p:
            continue
        canonical = BRAND_ALIAS_MAP.get(p.lower())
        if canonical:
            normalized.add(canonical)
        else:
            for alias, canon in BRAND_ALIAS_MAP.items():
                if alias in p.lower() or p.lower() in alias:
                    normalized.add(canon)
                    break
            else:
                normalized.add(p)
    return ";".join(sorted(normalized))


def score_row_quality(row: dict) -> tuple[int, list[str]]:
    """评估单行数据质量 0-100，返回 (分数, 扣分原因列表)"""
    score = 100
    issues = []

    if not row.get("国家", "").strip():
        score -= 20; issues.append("国家缺失")
    if not row.get("产品品线", "").strip():
        score -= 10; issues.append("品线缺失")
    if not row.get("负面原文摘录(本地语言)", "").strip():
        score -= 30; issues.append("原文缺失")
    elif len(row.get("负面原文摘录(本地语言)", "")) < 10:
        score -= 10; issues.append("原文过短(<10字)")
    if not row.get("负面主题", "").strip():
        score -= 15; issues.append("主题缺失")
    if not row.get("负面原文摘录(中文翻译)", "").strip():
        score -= 5; issues.append("中文翻译缺失")

    pain = row.get("痛点大类(功能/价格/体验/服务/安全)", "").strip()
    if pain and pain not in VALID_PAIN:
        score -= 10; issues.append(f"无效痛点: {pain}")

    intensity = row.get("负面强度(高/中/低)", "").strip()
    if intensity and intensity not in VALID_INTENSITY:
        score -= 5; issues.append(f"无效强度: {intensity}")

    seg = row.get("画像编码", "").strip()
    if not seg:
        score -= 10; issues.append("画像缺失")
    elif seg not in VALID_SEG:
        score -= 5; issues.append(f"非标画像: {seg}")

    if not row.get("来源URL", "").strip():
        score -= 5; issues.append("URL缺失")

    return max(0, score), issues


def process():
    if not TARGET_CSV.exists():
        print(f"[错误] {TARGET_CSV} 不存在")
        return

    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not rows:
        print("[跳过] CSV 无数据")
        return

    seg_updated = 0
    pain_updated = 0
    intensity_updated = 0
    competitor_updated = 0
    review_queue = []
    quality_scores = []
    seg_dist = Counter()

    for row in rows:
        combined = " ".join([
            row.get("负面原文摘录(本地语言)", ""),
            row.get("负面原文摘录(中文翻译)", ""),
            row.get("负面主题", ""),
        ])

        best_seg, seg_score = match_seg(combined)
        seg_dist[best_seg] += 1

        if not row.get("画像编码", "").strip():
            row["画像编码"] = best_seg
            row["画像名称"] = SEG_RULES[best_seg]["name"]
            row["生命周期"] = SEG_RULES[best_seg]["lifecycle"]
            seg_updated += 1

        pain = row.get("痛点大类(功能/价格/体验/服务/安全)", "").strip()
        if not pain or pain not in VALID_PAIN:
            new_pain = guess_pain(combined)
            row["痛点大类(功能/价格/体验/服务/安全)"] = new_pain
            pain_updated += 1

        intensity = row.get("负面强度(高/中/低)", "").strip()
        if not intensity or intensity not in VALID_INTENSITY:
            new_int = guess_intensity(combined)
            row["负面强度(高/中/低)"] = new_int
            intensity_updated += 1

        raw_comp = row.get("竞品关联品牌", "")
        norm_comp = normalize_competitors(raw_comp)
        if norm_comp != raw_comp:
            row["竞品关联品牌"] = norm_comp
            competitor_updated += 1

        q_score, q_issues = score_row_quality(row)
        quality_scores.append(q_score)

        needs_review = q_score < 60 or seg_score < 1.0
        if needs_review:
            review_queue.append({
                **row,
                "_质量分": q_score,
                "_质量问题": "; ".join(q_issues),
                "_SEG置信分": round(seg_score, 2),
                "_审核原因": "低质量" if q_score < 60 else "低SEG置信",
            })

    with open(TARGET_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if review_queue:
        rq_path = OUTPUT_DIR / "p3_review_queue.csv"
        rq_fields = list(fieldnames) + ["_质量分", "_质量问题", "_SEG置信分", "_审核原因"]
        with open(rq_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rq_fields)
            w.writeheader()
            w.writerows(review_queue)
        print(f"  审核工作单: {len(review_queue)} 条 → {rq_path}")

    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    high_q = sum(1 for s in quality_scores if s >= 80)
    mid_q = sum(1 for s in quality_scores if 60 <= s < 80)
    low_q = sum(1 for s in quality_scores if s < 60)

    report_lines = [
        "=" * 60,
        f"  P3 质量标注报告 ({date.today()})",
        "=" * 60,
        f"  总行数: {len(rows)}",
        f"",
        f"  自动补全:",
        f"    画像 (SEG): {seg_updated} 行",
        f"    痛点大类:   {pain_updated} 行",
        f"    负面强度:   {intensity_updated} 行",
        f"    竞品标准化: {competitor_updated} 行",
        f"",
        f"  画像分布:",
    ]
    for seg in sorted(SEG_RULES):
        cnt = seg_dist.get(seg, 0)
        pct = cnt / len(rows) * 100 if rows else 0
        report_lines.append(f"    {seg} ({SEG_RULES[seg]['name']}): {cnt} ({pct:.1f}%)")

    report_lines.extend([
        f"",
        f"  质量评分:",
        f"    平均分: {avg_quality:.1f}",
        f"    优质 (>=80): {high_q} ({high_q/len(rows)*100:.1f}%)",
        f"    中等 (60-79): {mid_q} ({mid_q/len(rows)*100:.1f}%)",
        f"    低质 (<60):   {low_q} ({low_q/len(rows)*100:.1f}%)",
        f"",
        f"  需人工审核: {len(review_queue)} 条",
        "=" * 60,
    ])

    report_text = "\n".join(report_lines)
    print(report_text)

    report_path = OUTPUT_DIR / "p3_quality_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)


if __name__ == "__main__":
    process()
