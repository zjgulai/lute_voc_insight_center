"""
Batch ingest feeding appliance & home travel brand reviews from Trustpilot.
Extends the breast pump collection to cover other product lines.
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

BRAND_CONFIG = {
    "Baby Brezza": {
        "slug": "babybrezza.com",
        "product_line": "\u5582\u517b\u7535\u5668",
    },
    "Tommee Tippee": {
        "slug": "tommeetippee.com",
        "product_line": "\u5582\u517b\u7535\u5668",
    },
    "BabyBjorn": {
        "slug": "babybjorn.com",
        "product_line": "\u5bb6\u5c45\u51fa\u884c",
    },
    "Bugaboo": {
        "slug": "bugaboo.com",
        "product_line": "\u5bb6\u5c45\u51fa\u884c",
    },
    "UPPAbaby": {
        "slug": "uppababy.com",
        "product_line": "\u5bb6\u5c45\u51fa\u884c",
    },
}

COUNTRY_FROM_CODE = {
    "US": ("\u7f8e\u56fd", "\u5317\u7f8e\u9ad8\u8d2d\u4e70\u529b\u533a"),
    "GB": ("\u82f1\u56fd", "\u897f\u6b27\u9ad8\u4fe1\u4efb\u8bba\u575b\u533a"),
    "CA": ("\u52a0\u62ff\u5927", "\u5317\u7f8e\u9ad8\u8d2d\u4e70\u529b\u533a"),
    "AU": ("\u6fb3\u5927\u5229\u4e9a", "\u82f1\u8054\u90a6\u4fe1\u4efb\u533a"),
    "DE": ("\u5fb7\u56fd", "\u897f\u6b27\u9ad8\u4fe1\u4efb\u8bba\u575b\u533a"),
    "FR": ("\u6cd5\u56fd", "\u897f\u6b27\u9ad8\u4fe1\u4efb\u8bba\u575b\u533a"),
}

PAIN_KEYWORDS = {
    "\u529f\u80fd": ["stopped working", "broken", "defect", "malfunction", "motor", "battery",
                     "pump", "heat", "warm", "steriliz", "blend"],
    "\u4ef7\u683c": ["expensive", "price", "cost", "overpriced", "waste of money", "rip off"],
    "\u4f53\u9a8c": ["leak", "size", "fit", "loud", "noise", "difficult", "complicated",
                     "messy", "hard to clean", "bulky"],
    "\u670d\u52a1": ["customer service", "support", "warranty", "return", "refund",
                     "shipping", "delivery", "replace"],
    "\u5b89\u5168": ["injury", "burn", "hot", "unsafe", "recall", "BPA", "chemical"],
}

INTENSITY_RULES = {
    "\u9ad8": ["terrible", "awful", "worst", "never", "do not buy", "waste", "dangerous",
               "useless", "garbage", "scam"],
    "\u4e2d": ["disappointed", "frustrated", "poor", "bad", "not recommend"],
    "\u4f4e": ["okay", "could be better", "minor"],
}

THEME_RULES = [
    ("\u4ea7\u54c1\u8010\u4e45\u6027\u5dee", ["broke", "fail", "stopped working", "last", "defect"]),
    ("\u6cc4\u6f0f\u95ee\u9898", ["leak", "spill"]),
    ("\u52a0\u70ed\u4e0d\u5747\u5300", ["heat", "warm", "uneven", "hot spot"]),
    ("\u6e05\u6d17\u56f0\u96be", ["clean", "hard to clean", "mold", "residue"]),
    ("\u5ba2\u670d\u54cd\u5e94\u5dee", ["customer service", "support", "response", "escalat"]),
    ("\u9000\u6b3e\u56f0\u96be", ["refund", "return", "money back"]),
    ("\u53d1\u8d27\u5ef6\u8fdf", ["delivery", "shipping", "dispatch", "arrive"]),
    ("\u4fdd\u4fee\u95ee\u9898", ["warranty", "guarantee"]),
    ("\u566a\u97f3\u5927", ["loud", "noise", "noisy"]),
    ("\u5c3a\u5bf8/\u914d\u4ef6\u4e0d\u5339\u914d", ["size", "fit", "compatible", "parts"]),
    ("\u4ef7\u683c\u4e0d\u503c", ["expensive", "overpriced", "not worth"]),
    ("\u5b89\u5168\u9690\u60a3", ["burn", "hot", "unsafe", "injury"]),
    ("\u7efc\u5408\u4f53\u9a8c\u5dee", []),
]


def guess_pain(text: str) -> str:
    t = text.lower()
    scores = {c: sum(1 for kw in kws if kw in t) for c, kws in PAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "\u4f53\u9a8c"


def guess_intensity(text: str) -> str:
    t = text.lower()
    for level, kws in INTENSITY_RULES.items():
        if any(kw in t for kw in kws):
            return level
    return "\u4e2d"


def guess_theme(text: str) -> str:
    t = text.lower()
    for theme, kws in THEME_RULES:
        if kws and any(kw in t for kw in kws):
            return theme
    return "\u7efc\u5408\u4f53\u9a8c\u5dee"


def guess_country(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(w in t for w in ["\u00a3", "nhs", "boots", "uk", "royal mail"]):
        return COUNTRY_FROM_CODE["GB"]
    if any(w in t for w in ["cad", "canada"]):
        return COUNTRY_FROM_CODE["CA"]
    if any(w in t for w in ["auspost", "australia"]):
        return COUNTRY_FROM_CODE["AU"]
    return COUNTRY_FROM_CODE["US"]


def parse_tp_markdown(md: str, brand: str, product_line: str) -> list[dict]:
    reviews = []
    sections = re.split(r'\[## ', md)
    for sec in sections[1:]:
        title_m = re.match(r'(.+?)\]\((.+?)\)', sec)
        if not title_m:
            continue
        title = title_m.group(1).strip()
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
            "platform_type": "\u7b2c\u4e09\u65b9\u8bc4\u6d4b\u7c7b",
            "platform": "Trustpilot",
            "pain": guess_pain(excerpt),
            "theme": guess_theme(excerpt),
            "excerpt": excerpt,
            "intensity": guess_intensity(excerpt),
            "brand": brand,
            "url": url,
            "batch": f"BATCH-TP-{brand.upper().replace(' ', '')}-001",
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
