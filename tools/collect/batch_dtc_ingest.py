"""
Batch DTC (Direct-to-Consumer) review collection.
Fetches product review pages from competitor brand official websites via r.jina.ai.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

LOG_FILE = Path(__file__).parent / "output" / "dtc_ingest_log.txt"

def log(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    try:
        print(msg, flush=True)
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
RAW_DIR = OUTPUT_DIR / "raw_dtc"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS_20 = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期",
    "痛点大类(功能/价格/体验/服务/安全)", "负面主题",
    "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌",
    "对应运营建议", "来源URL", "采集日期", "批次编码", "优先级",
]

DTC_TARGETS = [
    {
        "brand": "Momcozy",
        "product_line": "吸奶器",
        "urls": [
            "https://momcozy.com/products/momcozy-m5-wearable-breast-pump",
            "https://momcozy.com/products/momcozy-s12-pro-wearable-breast-pump",
            "https://momcozy.com/products/momcozy-m9-wearable-breast-pump",
        ],
        "platform": "Momcozy官网",
    },
    {
        "brand": "Elvie",
        "product_line": "吸奶器",
        "urls": [
            "https://www.elvie.com/en-us/shop/elvie-pump",
            "https://www.elvie.com/en-us/shop/elvie-stride",
        ],
        "platform": "Elvie官网",
    },
    {
        "brand": "Willow",
        "product_line": "吸奶器",
        "urls": [
            "https://www.willowpump.com/products/willow-go-wearable-breast-pump",
            "https://www.willowpump.com/products/willow-360-wearable-breast-pump",
        ],
        "platform": "Willow官网",
    },
    {
        "brand": "Baby Brezza",
        "product_line": "喂养电器",
        "urls": [
            "https://www.babybrezza.com/products/formula-pro-advanced",
            "https://www.babybrezza.com/products/bottle-washer-pro",
            "https://www.babybrezza.com/products/baby-brezza-sterilizer-dryer-advanced",
        ],
        "platform": "Baby Brezza官网",
    },
    {
        "brand": "Tommee Tippee",
        "product_line": "喂养电器",
        "urls": [
            "https://www.tommeetippee.com/en-us/product/perfect-prep-machine",
            "https://www.tommeetippee.com/en-us/product/made-for-me-single-electric-breast-pump",
        ],
        "platform": "Tommee Tippee官网",
    },
    {
        "brand": "Bugaboo",
        "product_line": "家居出行",
        "urls": [
            "https://www.bugaboo.com/us-en/strollers/bugaboo-fox5/",
            "https://www.bugaboo.com/us-en/strollers/bugaboo-dragonfly/",
            "https://www.bugaboo.com/us-en/strollers/bugaboo-butterfly/",
        ],
        "platform": "Bugaboo官网",
    },
    {
        "brand": "UPPAbaby",
        "product_line": "家居出行",
        "urls": [
            "https://uppababy.com/vista/",
            "https://uppababy.com/cruz/",
            "https://uppababy.com/minu/",
        ],
        "platform": "UPPAbaby官网",
    },
    {
        "brand": "Medela",
        "product_line": "吸奶器",
        "urls": [
            "https://www.medela.us/breastfeeding/products/breast-pumps/freestyle-flex",
            "https://www.medela.us/breastfeeding/products/breast-pumps/pump-in-style",
            "https://www.medela.us/breastfeeding/products/breast-pumps/sonata",
        ],
        "platform": "Medela官网",
    },
]

PAIN_KEYWORDS = {
    "功能": ["stopped working", "broken", "defect", "malfunction", "motor", "battery",
             "pump", "suction", "not work", "died", "broke", "fail", "doesn't work"],
    "价格": ["expensive", "price", "cost", "overpriced", "waste of money", "rip off", "not worth"],
    "体验": ["leak", "size", "fit", "loud", "noise", "difficult", "complicated",
             "messy", "hard to clean", "bulky", "uncomfortable", "heavy", "painful", "hurt"],
    "服务": ["customer service", "support", "warranty", "return", "refund",
             "shipping", "delivery", "replace", "response", "exchange"],
    "安全": ["injury", "burn", "hot", "unsafe", "recall", "BPA", "chemical", "mold"],
}

INTENSITY_RULES = {
    "高": ["terrible", "awful", "worst", "never", "do not buy", "waste", "dangerous",
           "useless", "garbage", "scam", "horrible", "zero stars", "disgusting"],
    "中": ["disappointed", "frustrated", "poor", "bad", "not recommend", "regret", "mediocre"],
    "低": ["okay", "could be better", "minor", "decent but"],
}

THEME_RULES = [
    ("产品耐久性差", ["broke", "fail", "stopped working", "last", "defect", "worn out", "died"]),
    ("吸力不足/下降", ["suction", "weak", "not strong enough", "lost suction"]),
    ("APP连接问题", ["app", "bluetooth", "connect", "pair", "wifi"]),
    ("泄漏问题", ["leak", "spill", "drip"]),
    ("噪音大", ["loud", "noise", "noisy", "sound"]),
    ("清洗困难", ["clean", "hard to clean", "mold", "residue"]),
    ("客服响应差", ["customer service", "support", "response", "escalat", "ignore", "unhelpful"]),
    ("退款困难", ["refund", "return", "money back"]),
    ("发货延迟", ["delivery", "shipping", "dispatch", "arrive", "wait", "delayed"]),
    ("保修问题", ["warranty", "guarantee", "replacement"]),
    ("尺寸/配件不匹配", ["size", "fit", "compatible", "parts", "flange"]),
    ("价格不值", ["expensive", "overpriced", "not worth", "too much"]),
    ("安全隐患", ["burn", "hot", "unsafe", "injury", "mold"]),
    ("充电/电池问题", ["battery", "charge", "charging", "power"]),
    ("舒适度差", ["painful", "uncomfortable", "hurt", "sore"]),
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
    if any(w in t for w in ["£", "nhs", "uk", "royal mail"]):
        return ("英国", "西欧高信任论坛区")
    if any(w in t for w in ["cad", "canada", "canadian"]):
        return ("加拿大", "北美高购买力区")
    if any(w in t for w in ["australia", "aud"]):
        return ("澳大利亚", "英联邦信任区")
    return ("美国", "北美高购买力区")


def extract_reviews_from_dtc(md: str) -> list[str]:
    """
    Extract individual review texts from a DTC product page markdown.
    DTC sites use various review widget formats; try multiple patterns.
    """
    reviews = []

    star_blocks = re.split(r'(?:★{1,2}[☆★]*|⭐{1,2}|(?:1|2)\s*(?:out of|/)\s*5)', md)
    if len(star_blocks) > 2:
        for block in star_blocks[1:]:
            text = block[:500].strip()
            text = re.sub(r'\n+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            if len(text) > 20:
                reviews.append(text[:200])

    review_patterns = [
        r'(?:Verified\s+(?:Buyer|Purchase|Reviewer))\s*\n+(.*?)(?=\n\n|\Z)',
        r'(?:Rated\s+[12]\s+out\s+of\s+5)\s*\n*(.*?)(?=Rated\s+\d|$)',
        r'(?:(?:1|2)\s+star(?:s)?)\s*\n*(.*?)(?=\d\s+star|$)',
    ]
    for pattern in review_patterns:
        matches = re.findall(pattern, md, re.DOTALL | re.IGNORECASE)
        for m in matches:
            text = re.sub(r'\n+', ' ', m).strip()
            text = re.sub(r'\s+', ' ', text)
            if 20 < len(text) < 500:
                reviews.append(text[:200])

    section_splits = re.split(
        r'\n(?:#{1,4}\s+|(?:\*\*|__))',
        md
    )
    neg_keywords = [
        "disappoint", "terrible", "awful", "worst", "broken", "defect",
        "waste", "return", "refund", "not recommend", "poor quality",
        "stopped working", "useless", "horrible", "doesn't work",
        "do not buy", "frustrated", "regret", "garbage",
    ]
    for section in section_splits:
        lower = section.lower()
        if any(kw in lower for kw in neg_keywords):
            text = re.sub(r'\n+', ' ', section).strip()
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\[.*?\]\(.*?\)', '', text)
            text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
            if 20 < len(text) < 500 and text not in reviews:
                reviews.append(text[:200])

    seen = set()
    unique = []
    for r in reviews:
        key = r[:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def fetch_page(url: str, brand: str, delay: float = 8.0) -> str | None:
    jina_url = f"https://r.jina.ai/{url}"
    log(f"  [FETCH] {url[:60]}...")

    try:
        req = urllib.request.Request(jina_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            md = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"    [WARN] Fetch failed: {e}")
        return None

    slug = re.sub(r'[^\w]', '_', url.split('/')[-1] or url.split('/')[-2])[:40]
    raw_path = RAW_DIR / f"{brand.replace(' ', '_')}_{slug}.md"
    raw_path.write_text(md, encoding="utf-8")
    log(f"    [SAVE] {raw_path.name} ({len(md)} bytes)")

    if delay > 0:
        log(f"    [WAIT] {delay}s ...")
        time.sleep(delay)

    return md


def process_brand(config: dict, delay: float = 8.0) -> list[dict]:
    brand = config["brand"]
    product_line = config["product_line"]
    platform = config["platform"]

    log(f"\n[BRAND] {brand} ({platform})")
    all_records = []

    for url in config["urls"]:
        md = fetch_page(url, brand, delay=delay)
        if not md:
            continue

        reviews = extract_reviews_from_dtc(md)
        log(f"    [EXTRACT] {len(reviews)} review snippets")

        for excerpt in reviews:
            country, cluster = guess_country(excerpt)
            all_records.append({
                "country": country,
                "cluster": cluster,
                "product_line": product_line,
                "platform_type": "竞品官方电商",
                "platform": platform,
                "pain": guess_pain(excerpt),
                "theme": guess_theme(excerpt),
                "excerpt": excerpt,
                "intensity": guess_intensity(excerpt),
                "brand": brand,
                "url": url,
                "batch": f"BATCH-DTC-{brand.upper().replace(' ', '')}-001",
            })

    log(f"  [TOTAL] {brand}: {len(all_records)} records")
    return all_records


def append_rows(rows: list[dict]) -> int:
    existing_urls_excerpts = set()
    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fns = reader.fieldnames
        for row in reader:
            key = row.get(fns[16], "") + "|" + row.get(fns[10], "")[:50]
            existing_urls_excerpts.add(key)

    new_rows = []
    for r in rows:
        key = r["url"] + "|" + r["excerpt"][:50]
        if key not in existing_urls_excerpts:
            new_rows.append(r)

    if not new_rows:
        log(f"[SKIP] All {len(rows)} already exist")
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
                r["batch"], "P2",
            ])

    log(f"[APPEND] {len(new_rows)} new rows")
    return len(new_rows)


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("", encoding="utf-8")
    log("[START] DTC batch ingest")

    all_records = []
    for config in DTC_TARGETS:
        records = process_brand(config, delay=8.0)
        all_records.extend(records)

    log(f"\n{'='*60}")
    log(f"[TOTAL] Collected {len(all_records)} DTC review snippets")

    if all_records:
        added = append_rows(all_records)
        log(f"[DONE] Appended {added} new rows to CSV")
    else:
        log("[WARN] No DTC reviews collected")


if __name__ == "__main__":
    main()
