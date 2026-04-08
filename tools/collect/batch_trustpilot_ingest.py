"""
Batch ingest Trustpilot 1-star reviews into dim_voc_negative_extract.csv.
Fetches pages via r.jina.ai, parses markdown, maps to standard schema.
Designed for rate-limited, interval-controlled collection.
"""
from __future__ import annotations

import csv
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.collect.brand_scope_config import FROZEN_BRANDS_BY_LINE, TRUSTPILOT_SLUGS

TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
RAW_DIR = OUTPUT_DIR / "raw_trustpilot"

HEADERS = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期",
    "痛点大类(功能/价格/体验/服务/安全)", "负面主题",
    "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌",
    "对应运营建议", "来源URL", "采集日期", "批次编码", "优先级",
]

COUNTRY_FROM_CODE = {
    "US": ("美国", "北美高购买力区"),
    "GB": ("英国", "西欧高信任论坛区"),
    "CA": ("加拿大", "北美高购买力区"),
    "AU": ("澳大利亚", "英联邦信任区"),
    "DE": ("德国", "西欧高信任论坛区"),
    "FR": ("法国", "西欧高信任论坛区"),
}

BRAND_PRODUCT_LINE = {
    brand.lower(): product_line
    for product_line, brands in FROZEN_BRANDS_BY_LINE.items()
    for brand in brands
}

PAIN_KEYWORDS = {
    "功能": ["suction", "pump", "motor", "battery", "connect", "app", "firmware",
             "stopped working", "malfunction", "broken", "dead", "defect", "fail"],
    "价格": ["expensive", "price", "cost", "money", "overpriced", "waste of money",
             "refund", "rip off", "not worth"],
    "体验": ["leak", "size", "fit", "flange", "painful", "uncomfortable", "loud",
             "noise", "heavy", "bulky", "difficult", "hard to clean"],
    "服务": ["customer service", "support", "warranty", "return", "refund", "replace",
             "shipping", "delivery", "dispatch", "response", "email", "escalat"],
    "安全": ["injury", "hurt", "burn", "allergic", "reaction", "mastitis", "infection",
             "pain", "bleed", "unsafe"],
}

INTENSITY_RULES = {
    "高": ["terrible", "awful", "worst", "never", "do not buy", "waste", "appalling",
            "disgusting", "furious", "scam", "garbage", "rubbish", "useless"],
    "中": ["disappointed", "frustrated", "poor", "bad", "not recommend", "annoying",
            "mediocre", "subpar"],
    "低": ["okay", "average", "could be better", "minor"],
}


def guess_pain(text: str) -> str:
    text_l = text.lower()
    scores = {}
    for cat, keywords in PAIN_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in text_l)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "体验"


def guess_intensity(text: str) -> str:
    text_l = text.lower()
    for level, keywords in INTENSITY_RULES.items():
        if any(kw in text_l for kw in keywords):
            return level
    return "中"


def guess_country(reviewer_info: str) -> tuple[str, str]:
    for code, (name, cluster) in COUNTRY_FROM_CODE.items():
        if code in reviewer_info:
            return name, cluster
    return "美国", "北美高购买力区"


def guess_theme(text: str) -> str:
    text_l = text.lower()
    themes = [
        ("产品耐久性差", ["broke", "fail", "stopped working", "dead", "defect", "last"]),
        ("泄漏问题", ["leak", "spill", "overflow"]),
        ("吸力不足/下降", ["suction", "weak", "barely"]),
        ("配件缺货", ["out of stock", "spare part", "replacement part", "unavailable"]),
        ("退款困难", ["refund", "return", "money back"]),
        ("保修问题", ["warranty", "receipt", "proof of purchase"]),
        ("客服响应差", ["customer service", "support", "response", "escalat", "ignored"]),
        ("发货延迟", ["delivery", "shipping", "dispatch", "arrive", "late"]),
        ("噪音大", ["loud", "noise", "noisy"]),
        ("电池续航短", ["battery", "charge", "dies"]),
        ("尺寸不合", ["size", "fit", "flange", "too big", "too small"]),
        ("APP连接问题", ["app", "connect", "bluetooth", "firmware"]),
        ("价格不值", ["expensive", "overpriced", "not worth", "waste of money"]),
        ("退换政策不合理", ["return policy", "exchange policy", "misleading"]),
    ]
    for theme, keywords in themes:
        if any(kw in text_l for kw in keywords):
            return theme
    return "综合体验差"


def translate_excerpt(text: str) -> str:
    """Generate a simplified Chinese summary (rule-based approximation)."""
    text_l = text.lower()
    translations = {
        "broke": "产品损坏",
        "stopped working": "停止工作",
        "leak": "泄漏",
        "terrible quality": "质量糟糕",
        "waste of money": "浪费钱",
        "disappointed": "失望",
        "customer service": "客服",
        "refund": "退款",
        "warranty": "保修",
        "delivery": "配送",
        "shipping": "发货",
    }
    parts = []
    for en, zh in translations.items():
        if en in text_l:
            parts.append(zh)
    if not parts:
        return text[:80] + "..."
    return "；".join(parts[:4])


def parse_trustpilot_markdown(md_text: str, brand: str) -> list[dict]:
    """Parse Jina-fetched Trustpilot markdown into review records."""
    reviews = []
    sections = re.split(r'\[## ', md_text)

    for section in sections[1:]:
        title_match = re.match(r'(.+?)\]\((.+?)\)', section)
        if not title_match:
            continue

        title = title_match.group(1).strip()
        url = title_match.group(2).strip()
        body_text = section[title_match.end():]

        date_match = re.search(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
            body_text)
        review_date = date_match.group(0) if date_match else ""

        reply_start = body_text.find("Hi,") if "Hi," in body_text else body_text.find("Dear ")
        if reply_start == -1:
            reply_start = body_text.find("Hi there")
        if reply_start == -1:
            reply_start = body_text.find("Thank you for")

        review_body = body_text[:reply_start].strip() if reply_start > 0 else body_text.strip()
        review_body = re.sub(r'\n{3,}', '\n\n', review_body)

        clean = re.sub(r'\*+', '', review_body)
        clean = re.sub(r'\n+', ' ', clean).strip()
        clean = re.sub(r'\s+', ' ', clean)

        if date_match:
            idx = clean.find(date_match.group(0))
            if idx > 0:
                clean = clean[:idx].strip()

        reviewer_match = re.search(r'(\w+)\s+(US|GB|CA|AU|DE|FR|ES)', section[:200])
        reviewer_info = reviewer_match.group(0) if reviewer_match else ""
        country, cluster = guess_country(reviewer_info)

        excerpt = clean[:200] if len(clean) > 200 else clean
        if not excerpt or len(excerpt) < 10:
            continue

        reviews.append({
            "国家": country,
            "区域cluster": cluster,
            "产品品线": BRAND_PRODUCT_LINE.get(brand.lower(), "吸奶器"),
            "平台类型": "第三方评测类",
            "平台": "Trustpilot",
            "画像编码": "",
            "画像名称": "",
            "生命周期": "",
            "痛点大类(功能/价格/体验/服务/安全)": guess_pain(excerpt),
            "负面主题": guess_theme(excerpt),
            "负面原文摘录(本地语言)": excerpt,
            "负面原文摘录(中文翻译)": translate_excerpt(excerpt),
            "频次估算": "",
            "负面强度(高/中/低)": guess_intensity(excerpt),
            "竞品关联品牌": brand,
            "对应运营建议": "",
            "来源URL": url,
            "采集日期": str(date.today()),
            "批次编码": f"BATCH-TP-{brand.upper()}-001",
            "优先级": "P1",
        })

    return reviews


def fetch_and_parse(trustpilot_slug: str, brand: str,
                    stars: int = 1, delay: float = 6.0) -> list[dict]:
    """Fetch Trustpilot page via Jina and parse reviews."""
    url = f"https://r.jina.ai/https://www.trustpilot.com/review/{trustpilot_slug}?stars={stars}"
    print(f"[FETCH] {brand} ({stars}-star) from {trustpilot_slug} ...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            md_text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] Fetch failed: {e}")
        return []

    raw_path = RAW_DIR / f"{brand}_{stars}star.md"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(md_text, encoding="utf-8")
    print(f"  [SAVE] Raw markdown -> {raw_path.name} ({len(md_text)} bytes)")

    reviews = parse_trustpilot_markdown(md_text, brand)
    print(f"  [PARSE] Extracted {len(reviews)} review records")

    if delay > 0:
        print(f"  [WAIT] Sleeping {delay}s ...")
        time.sleep(delay)

    return reviews


def append_to_csv(rows: list[dict]):
    """Append new rows to the existing dim_voc_negative_extract.csv."""
    existing_urls = set()
    if TARGET_CSV.exists():
        with open(TARGET_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_urls.add(row.get("来源URL", ""))

    new_rows = [r for r in rows if r.get("来源URL", "") not in existing_urls]
    if not new_rows:
        print(f"[SKIP] No new rows to append (all {len(rows)} already exist)")
        return 0

    with open(TARGET_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        for row in new_rows:
            writer.writerow(row)

    print(f"[APPEND] Added {len(new_rows)} new rows to {TARGET_CSV.name}")
    return len(new_rows)


TARGETS = [(slug, brand) for brand, slug in TRUSTPILOT_SLUGS.items()]


def main():
    all_reviews = []
    for slug, brand in TARGETS:
        for stars in [1, 2]:
            reviews = fetch_and_parse(slug, brand, stars=stars, delay=7.0)
            all_reviews.extend(reviews)

    if all_reviews:
        added = append_to_csv(all_reviews)
        print(f"\n{'='*60}")
        print(f"[DONE] Total fetched: {len(all_reviews)}, new appended: {added}")
    else:
        print("[WARN] No reviews collected")

    report_path = OUTPUT_DIR / "trustpilot_ingest_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Trustpilot Ingest Report - {date.today()}\n")
        f.write(f"{'='*50}\n")
        f.write(f"Total reviews collected: {len(all_reviews)}\n")
        brands = {}
        for r in all_reviews:
            b = r.get("竞品关联品牌", "Unknown")
            brands[b] = brands.get(b, 0) + 1
        for b, c in sorted(brands.items(), key=lambda x: -x[1]):
            f.write(f"  {b}: {c}\n")
        countries = {}
        for r in all_reviews:
            c = r.get("国家", "Unknown")
            countries[c] = countries.get(c, 0) + 1
        f.write(f"\nCountry distribution:\n")
        for c, n in sorted(countries.items(), key=lambda x: -x[1]):
            f.write(f"  {c}: {n}\n")
    print(f"[REPORT] {report_path}")


if __name__ == "__main__":
    main()
