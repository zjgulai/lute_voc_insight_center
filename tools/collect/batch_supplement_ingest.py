"""
Supplemental collection: BabyBjorn UK + Philips Avent from Trustpilot.
"""
from __future__ import annotations

import csv
import re
import time
import urllib.request
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
RAW_DIR = OUTPUT_DIR / "raw_trustpilot"

COUNTRY_FROM_CODE = {
    "US": ("美国", "北美高购买力区"),
    "GB": ("英国", "西欧高信任论坛区"),
    "CA": ("加拿大", "北美高购买力区"),
    "AU": ("澳大利亚", "英联邦信任区"),
    "DE": ("德国", "西欧高信任论坛区"),
    "FR": ("法国", "西欧高信任论坛区"),
    "NL": ("荷兰", "西欧高信任论坛区"),
    "SE": ("瑞典", "西欧高信任论坛区"),
}

BRAND_CONFIG = {
    "BabyBjorn UK": {
        "slug": "babybjorn.co.uk",
        "product_line": "家居出行",
    },
    "Philips Avent": {
        "slug": "philips-avent.com",
        "product_line": "喂养电器",
    },
    "Philips Avent UK": {
        "slug": "philips.co.uk",
        "product_line": "喂养电器",
    },
}

PAIN_KEYWORDS = {
    "功能": ["stopped working", "broken", "defect", "malfunction", "motor", "battery",
             "pump", "heat", "warm", "steriliz", "blend", "buckle", "strap"],
    "价格": ["expensive", "price", "cost", "overpriced", "waste of money", "rip off"],
    "体验": ["leak", "size", "fit", "loud", "noise", "difficult", "complicated",
             "messy", "hard to clean", "bulky", "uncomfortable", "heavy"],
    "服务": ["customer service", "support", "warranty", "return", "refund",
             "shipping", "delivery", "replace", "response"],
    "安全": ["injury", "burn", "hot", "unsafe", "recall", "BPA", "chemical"],
}

INTENSITY_RULES = {
    "高": ["terrible", "awful", "worst", "never", "do not buy", "waste", "dangerous",
           "useless", "garbage", "scam", "disgusting"],
    "中": ["disappointed", "frustrated", "poor", "bad", "not recommend", "regret"],
    "低": ["okay", "could be better", "minor", "slightly"],
}

THEME_RULES = [
    ("产品耐久性差", ["broke", "fail", "stopped working", "last", "defect", "worn"]),
    ("泄漏问题", ["leak", "spill"]),
    ("安全扣/带问题", ["buckle", "strap", "harness", "click"]),
    ("清洗困难", ["clean", "hard to clean", "mold", "residue"]),
    ("客服响应差", ["customer service", "support", "response", "escalat", "ignore"]),
    ("退款困难", ["refund", "return", "money back"]),
    ("发货延迟", ["delivery", "shipping", "dispatch", "arrive", "wait"]),
    ("保修问题", ["warranty", "guarantee"]),
    ("噪音大", ["loud", "noise", "noisy"]),
    ("尺寸/配件不匹配", ["size", "fit", "compatible", "parts"]),
    ("价格不值", ["expensive", "overpriced", "not worth"]),
    ("安全隐患", ["burn", "hot", "unsafe", "injury"]),
    ("综合体验差", []),
]


def guess_pain(text: str) -> str:
    t = text.lower()
    scores = {c: sum(1 for kw in kws if kw in t) for c, kws in PAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "体验"


def guess_intensity(text: str) -> str:
    t = text.lower()
    for level, kws in INTENSITY_RULES.items():
        if any(kw in t for kw in kws):
            return level
    return "中"


def guess_theme(text: str) -> str:
    t = text.lower()
    for theme, kws in THEME_RULES:
        if kws and any(kw in t for kw in kws):
            return theme
    return "综合体验差"


def guess_country(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(w in t for w in ["£", "nhs", "boots", "uk", "royal mail"]):
        return COUNTRY_FROM_CODE["GB"]
    if any(w in t for w in ["cad", "canada", "canadian"]):
        return COUNTRY_FROM_CODE["CA"]
    if any(w in t for w in ["auspost", "australia", "aud"]):
        return COUNTRY_FROM_CODE["AU"]
    if any(w in t for w in ["€", "euro"]):
        return COUNTRY_FROM_CODE["DE"]
    return COUNTRY_FROM_CODE["US"]


def parse_tp_markdown(md: str, brand: str, product_line: str) -> list[dict]:
    reviews = []
    sections = re.split(r'\[## ', md)
    for sec in sections[1:]:
        title_m = re.match(r'(.+?)\]\((.+?)\)', sec)
        if not title_m:
            continue
        url = title_m.group(2).strip()
        body = sec[title_m.end():]

        reply_markers = ["Hi,", "Hi there", "Dear ", "Thank you for"]
        reply_pos = len(body)
        for marker in reply_markers:
            idx = body.find(marker)
            if 0 < idx < reply_pos:
                reply_pos = idx

        review_text = body[:reply_pos].strip()
        review_text = re.sub(r'\n+', ' ', review_text).strip()
        review_text = re.sub(r'\s+', ' ', review_text)

        date_m = re.search(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
            review_text)
        if date_m:
            review_text = review_text[:review_text.find(date_m.group(0))].strip()

        excerpt = review_text[:200] if len(review_text) > 200 else review_text
        if not excerpt or len(excerpt) < 10:
            continue

        country, cluster = guess_country(excerpt)

        reviews.append({
            "country": country,
            "cluster": cluster,
            "product_line": product_line,
            "platform_type": "第三方评测类",
            "platform": "Trustpilot",
            "pain": guess_pain(excerpt),
            "theme": guess_theme(excerpt),
            "excerpt": excerpt,
            "intensity": guess_intensity(excerpt),
            "brand": brand,
            "url": url,
            "batch": f"BATCH-TP-{brand.upper().replace(' ', '')}-002",
        })
    return reviews


def fetch_brand(slug: str, brand: str, product_line: str,
                stars: int = 1, delay: float = 8.0) -> list[dict]:
    url = f"https://r.jina.ai/https://www.trustpilot.com/review/{slug}?stars={stars}"
    print(f"[FETCH] {brand} ({stars}-star) ...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            md = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] Fetch failed: {e}")
        return []

    raw_path = RAW_DIR / f"{brand.replace(' ', '_')}_{stars}star.md"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(md, encoding="utf-8")
    print(f"  [SAVE] {raw_path.name} ({len(md)} bytes)")

    reviews = parse_tp_markdown(md, brand, product_line)
    print(f"  [PARSE] {len(reviews)} records")

    if delay > 0:
        print(f"  [WAIT] {delay}s ...")
        time.sleep(delay)
    return reviews


def append_rows(rows: list[dict]):
    existing_urls = set()
    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            url_key = fieldnames[16] if len(fieldnames) > 16 else None
            if url_key:
                existing_urls.add(row.get(url_key, ""))

    new_rows = [r for r in rows if r.get("url", "") not in existing_urls]
    if not new_rows:
        print(f"[SKIP] All {len(rows)} already exist")
        return 0

    with open(TARGET_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        for r in new_rows:
            writer.writerow([
                r["country"], r["cluster"], r["product_line"],
                r["platform_type"], r["platform"],
                "", "", "",
                r["pain"], r["theme"],
                r["excerpt"], "",
                "", r["intensity"], r["brand"],
                "", r["url"], str(date.today()),
                r["batch"], "P1",
            ])

    print(f"[APPEND] {len(new_rows)} new rows")
    return len(new_rows)


def main():
    all_reviews = []
    for brand, cfg in BRAND_CONFIG.items():
        for stars in [1, 2]:
            reviews = fetch_brand(cfg["slug"], brand, cfg["product_line"],
                                  stars=stars, delay=8.0)
            all_reviews.extend(reviews)

    if all_reviews:
        added = append_rows(all_reviews)
        print(f"\n{'='*60}")
        print(f"[DONE] Fetched: {len(all_reviews)}, appended: {added}")
    else:
        print("[WARN] No reviews collected")


if __name__ == "__main__":
    main()
