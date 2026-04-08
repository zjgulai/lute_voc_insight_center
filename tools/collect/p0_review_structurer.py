"""
P0 采集脚本 2/4 — 评论结构化器

功能：
  将手动或半自动采集到的原始评论文本，结构化为 dim_voc_negative_extract.csv 的标准行。
  支持两种输入模式：
    1. 交互式逐条录入（命令行）
    2. 批量导入 JSON 文件

输出：
  追加到 data/delivery/tables/dim_voc_negative_extract.csv
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
BATCH_INPUT_DIR = Path(__file__).parent / "input"

CLUSTER_MAP = {
    "US": "北美高购买力区", "CA": "北美高购买力区",
    "GB": "西欧高信任论坛区", "DE": "西欧高信任论坛区",
    "FR": "西欧高信任论坛区", "ES": "西欧高信任论坛区",
    "MX": "拉美社媒口碑区",
    "AE": "中东视觉社媒区", "SA": "中东视觉社媒区",
    "AU": "英语成熟市场",
}

COUNTRY_CODE_MAP = {
    "US": "美国", "CA": "加拿大", "GB": "英国", "DE": "德国",
    "FR": "法国", "ES": "西班牙", "MX": "墨西哥",
    "AE": "阿联酋", "AU": "澳大利亚", "SA": "沙特阿拉伯",
}

VALID_PAIN = {"功能", "价格", "体验", "服务", "安全"}
VALID_INTENSITY = {"高", "中", "低"}

CSV_FIELDNAMES = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期",
    "痛点大类(功能/价格/体验/服务/安全)",
    "负面主题", "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌",
    "对应运营建议", "来源URL", "采集日期", "批次编码", "优先级",
]

SEG_KEYWORDS = {
    "SEG01": {
        "name": "产后建奶新手妈妈",
        "lifecycle": "产后0-3月",
        "keywords": [
            "newborn", "first time", "ftm", "new mom", "postpartum",
            "新生儿", "新手", "第一次", "刚生",
            "primipare", "nouveau-né", "Erstgebärende", "recién nacida",
        ],
    },
    "SEG02": {
        "name": "返岗背奶效率妈妈",
        "lifecycle": "产后3-12月",
        "keywords": [
            "work", "office", "commute", "back to work", "job",
            "上班", "返岗", "办公室",
            "travail", "bureau", "Arbeit", "Büro", "trabajo", "oficina",
        ],
    },
    "SEG03": {
        "name": "高频泵奶复购家庭",
        "lifecycle": "产后0-12月",
        "keywords": [
            "replace", "replacement", "second", "again", "reorder",
            "复购", "二胎", "换",
            "remplacement", "Ersatz", "reemplazo", "repuesto",
        ],
    },
}


def match_segment(text: str) -> tuple[str, str, str]:
    """基于关键词匹配画像编码，返回 (seg_code, seg_name, lifecycle)"""
    lower = text.lower()
    scores = {}
    for seg, info in SEG_KEYWORDS.items():
        score = sum(1 for kw in info["keywords"] if kw.lower() in lower)
        scores[seg] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "SEG01"

    info = SEG_KEYWORDS[best]
    return best, info["name"], info["lifecycle"]


def guess_pain_category(text: str) -> str:
    """根据内容猜测痛点大类"""
    lower = text.lower()
    rules = [
        ("安全", ["safe", "safety", "bpa", "toxic", "smell", "chemical", "sicher", "sécur", "segur"]),
        ("价格", ["price", "expensive", "cost", "money", "cheap", "prix", "Preis", "precio", "refund"]),
        ("服务", ["service", "support", "warranty", "return", "customer", "售后", "service", "Garantie"]),
        ("功能", ["suction", "power", "motor", "battery", "broken", "defect", "Saugleistung", "aspiration", "succión"]),
        ("体验", ["pain", "noise", "loud", "uncomfortable", "flange", "size", "clean", "douleur", "Schmerz", "dolor"]),
    ]
    for cat, keywords in rules:
        if any(kw in lower for kw in keywords):
            return cat
    return "体验"


def guess_intensity(text: str) -> str:
    """根据情绪强度词猜测负面强度"""
    lower = text.lower()
    high = ["terrible", "worst", "useless", "dangerous", "horrible", "waste", "never again", "furchtbar", "horrible"]
    low = ["minor", "slightly", "okay", "ok", "fine", "acceptable", "légèrement", "etwas"]

    if any(w in lower for w in high):
        return "高"
    if any(w in lower for w in low):
        return "低"
    return "中"


def extract_competitors(text: str) -> str:
    """从评论中提取竞品品牌"""
    brands = [
        "Spectra", "Medela", "Elvie", "Willow", "Momcozy",
        "Philips Avent", "Lansinoh", "Haakaa", "Motif",
        "NUK", "Chicco", "Pigeon", "Dr. Brown",
    ]
    found = [b for b in brands if b.lower() in text.lower()]
    return ";".join(found) if found else ""


def structure_review(raw: dict) -> dict:
    """将原始评论字典转为 CSV 行字典"""
    country_code = raw.get("country_code", "US")
    country = raw.get("country", COUNTRY_CODE_MAP.get(country_code, ""))
    cluster = raw.get("cluster", CLUSTER_MAP.get(country_code, ""))
    platform = raw.get("platform", f"Amazon.{country_code.lower()}")
    original = raw.get("original_text", "")
    translated = raw.get("translated_text", "")

    combined = f"{original} {translated}"
    seg_code, seg_name, lifecycle = match_segment(combined)

    seg_code = raw.get("segment_code", seg_code)
    if seg_code in SEG_KEYWORDS:
        seg_name = SEG_KEYWORDS[seg_code]["name"]
        lifecycle = SEG_KEYWORDS[seg_code]["lifecycle"]

    pain = raw.get("pain_category", guess_pain_category(combined))
    if pain not in VALID_PAIN:
        pain = "体验"

    intensity = raw.get("intensity", guess_intensity(combined))
    if intensity not in VALID_INTENSITY:
        intensity = "中"

    return {
        "国家": country,
        "区域cluster": cluster,
        "产品品线": raw.get("product_line", "吸奶器"),
        "平台类型": raw.get("platform_type", "电商评论类"),
        "平台": platform,
        "画像编码": seg_code,
        "画像名称": seg_name,
        "生命周期": lifecycle,
        "痛点大类(功能/价格/体验/服务/安全)": pain,
        "负面主题": raw.get("theme", ""),
        "负面原文摘录(本地语言)": original,
        "负面原文摘录(中文翻译)": translated,
        "频次估算": raw.get("frequency", 1),
        "负面强度(高/中/低)": intensity,
        "竞品关联品牌": raw.get("competitor", extract_competitors(combined)),
        "对应运营建议": raw.get("suggestion", ""),
        "来源URL": raw.get("url", ""),
        "采集日期": raw.get("date", str(date.today())),
        "批次编码": raw.get("batch", f"BATCH-P0-{country_code}-001"),
        "优先级": raw.get("priority", "P0"),
    }


def append_to_csv(rows: list[dict]):
    """追加结构化行到目标 CSV"""
    file_exists = TARGET_CSV.exists() and TARGET_CSV.stat().st_size > 0
    with open(TARGET_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ 已追加 {len(rows)} 行到 {TARGET_CSV.name}")


def load_batch_json(json_path: Path) -> list[dict]:
    """
    从 JSON 文件批量导入评论。

    JSON 格式示例:
    [
      {
        "country_code": "US",
        "platform": "Amazon.com",
        "original_text": "The flange size was wrong...",
        "translated_text": "罩杯尺码不对...",
        "theme": "罩杯不适配",
        "url": "https://www.amazon.com/dp/...",
        "frequency": 5
      }
    ]
    """
    with open(json_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    structured = [structure_review(r) for r in raw_list]
    print(f"[批量导入] {json_path.name}: {len(raw_list)} 条评论 → {len(structured)} 条结构化")
    return structured


def interactive_mode():
    """交互式逐条录入"""
    print("=" * 60)
    print("P0 评论结构化器 — 交互模式")
    print("输入 q 退出，输入 s 保存当前批次")
    print("=" * 60)

    buffer: list[dict] = []
    while True:
        print(f"\n--- 第 {len(buffer)+1} 条 ---")
        country_code = input("国家编码 (US/CA/GB/DE/FR/ES/MX/AE/AU/SA): ").strip().upper()
        if country_code == "Q":
            break

        original = input("原文: ").strip()
        if original.lower() in ("q", "s"):
            if original.lower() == "s" and buffer:
                append_to_csv(buffer)
                buffer = []
            break

        translated = input("中文翻译: ").strip()
        theme = input("负面主题 (简短): ").strip()
        url = input("来源 URL: ").strip()

        raw = {
            "country_code": country_code,
            "original_text": original,
            "translated_text": translated,
            "theme": theme,
            "url": url,
        }

        structured = structure_review(raw)
        seg = structured["画像编码"]
        pain = structured["痛点大类(功能/价格/体验/服务/安全)"]
        intensity = structured["负面强度(高/中/低)"]
        print(f"  → 自动匹配: 画像={seg}, 痛点={pain}, 强度={intensity}")

        confirm = input("  确认添加? (y/n/修改画像 SEG01-03): ").strip()
        if confirm.startswith("SEG"):
            structured["画像编码"] = confirm
            if confirm in SEG_KEYWORDS:
                structured["画像名称"] = SEG_KEYWORDS[confirm]["name"]
                structured["生命周期"] = SEG_KEYWORDS[confirm]["lifecycle"]

        if confirm.lower() != "n":
            buffer.append(structured)
            print(f"  ✓ 已缓存（共 {len(buffer)} 条）")

    if buffer:
        save = input(f"\n保存 {len(buffer)} 条到 CSV? (y/n): ").strip()
        if save.lower() == "y":
            append_to_csv(buffer)


def main():
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
        if json_path.exists():
            rows = load_batch_json(json_path)
            if rows:
                append_to_csv(rows)
        else:
            print(f"文件不存在: {json_path}")
            sys.exit(1)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
