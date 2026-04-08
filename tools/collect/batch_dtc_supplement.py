"""
Supplement DTC review collection:
1. More Momcozy products via Okendo API
2. Parse community discussion pages about competitor DTC products
3. Fetch additional Trustpilot pages for brands with low coverage
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
RAW_DIR = OUTPUT_DIR / "raw_dtc"
RAW_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUTPUT_DIR / "dtc_supplement_log.txt"


def log(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    try:
        print(msg, flush=True)
    except Exception:
        pass


PAIN_KEYWORDS = {
    "功能": ["stopped working", "broken", "defect", "malfunction", "motor", "battery",
             "pump", "suction", "not work", "died", "broke", "fail", "doesn't work",
             "won't turn on", "quit", "stopped", "dead", "half an ounce"],
    "价格": ["expensive", "price", "cost", "overpriced", "waste of money", "rip off",
             "not worth", "$375", "$300", "$250"],
    "体验": ["leak", "size", "fit", "loud", "noise", "difficult", "complicated",
             "messy", "hard to clean", "bulky", "uncomfortable", "heavy", "painful",
             "hurt", "small", "large", "awkward", "flange"],
    "服务": ["customer service", "support", "warranty", "return", "refund",
             "shipping", "delivery", "replace", "response", "exchange", "unhelpful"],
    "安全": ["injury", "burn", "hot", "unsafe", "recall", "BPA", "chemical", "mold"],
}

INTENSITY_RULES = {
    "高": ["terrible", "awful", "worst", "never", "do not buy", "waste", "dangerous",
           "useless", "garbage", "scam", "horrible", "zero stars", "disgusting",
           "regret", "hate", "trash"],
    "中": ["disappointed", "frustrated", "poor", "bad", "not recommend", "mediocre",
           "annoying", "issue", "problem"],
    "低": ["okay", "could be better", "minor", "decent but", "not great"],
}

THEME_RULES = [
    ("产品耐久性差", ["broke", "fail", "stopped working", "last", "defect", "worn out", "died", "quit"]),
    ("吸力不足/下降", ["suction", "weak", "not strong enough", "lost suction", "half an ounce", "output"]),
    ("APP连接问题", ["app", "bluetooth", "connect", "pair", "wifi"]),
    ("泄漏问题", ["leak", "spill", "drip"]),
    ("噪音大", ["loud", "noise", "noisy", "sound"]),
    ("清洗困难", ["clean", "hard to clean", "mold", "residue"]),
    ("客服响应差", ["customer service", "support", "response", "escalat", "ignore", "unhelpful"]),
    ("退款困难", ["refund", "return", "money back", "won't let you return"]),
    ("发货延迟", ["delivery", "shipping", "dispatch", "arrive", "wait", "delayed"]),
    ("保修问题", ["warranty", "guarantee", "replacement"]),
    ("尺寸/配件不匹配", ["size", "fit", "compatible", "parts", "flange"]),
    ("价格不值", ["expensive", "overpriced", "not worth", "too much", "$375"]),
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
    if any(w in t for w in ["uk", "nhs", "boots", "babycentre"]):
        return ("英国", "西欧高信任论坛区")
    if any(w in t for w in ["cad", "canada", "canadian"]):
        return ("加拿大", "北美高购买力区")
    if any(w in t for w in ["australia", "aud"]):
        return ("澳大利亚", "英联邦信任区")
    return ("美国", "北美高购买力区")


def fetch_jina(url: str, output_name: str, delay: float = 8.0) -> str | None:
    jina_url = f"https://r.jina.ai/{url}"
    log(f"  [FETCH] {url[:60]}...")
    try:
        req = urllib.request.Request(jina_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            md = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"    [WARN] Fetch failed: {e}")
        return None

    raw_path = RAW_DIR / output_name
    raw_path.write_text(md, encoding="utf-8")
    log(f"    [SAVE] {output_name} ({len(md)} bytes)")
    if delay > 0:
        time.sleep(delay)
    return md


# ---- Phase 1: More Momcozy products via Okendo API ----

OKENDO_STORE_ID = "fd7a9ef8-afae-47de-a7c1-4ca9730e4d32"

EXTRA_MOMCOZY_PRODUCTS = [
    ("shopify-7918308491462", "M6 Mobile Breast Pump", "吸奶器"),
    ("shopify-8533303050438", "S12 Pro Wearable Breast Pump", "吸奶器"),
    ("shopify-8595612803270", "Kneading Nursing Pillow", "喂养电器"),
]


def fetch_okendo_low(product_id: str, product_name: str) -> list[dict]:
    url = f"https://api.okendo.io/v1/stores/{OKENDO_STORE_ID}/products/{product_id}/reviews?limit=50&orderBy=rating%20asc"
    log(f"  [OKENDO] {product_name} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log(f"    [WARN] {e}")
        return []

    reviews = []
    for r in data.get("reviews", []):
        rating = r.get("rating", 5)
        if rating <= 3:
            body = r.get("body", "")
            title = r.get("title", "")
            text = f"{title}. {body}" if title else body
            if len(text) > 20:
                reviews.append(text[:300])

    log(f"    [FOUND] {len(reviews)} negative reviews")
    return reviews


# ---- Phase 2: Parse community pages ----

COMMUNITY_SOURCES = [
    {
        "brand": "Elvie",
        "product_line": "吸奶器",
        "platform": "Elvie官网(用户社区)",
        "file": "elvie_whattoexpect_garbage.md",
        "url": "https://community.whattoexpect.com/forums/january-2023-babies/topic/elvie-is-garbage-147893470.html",
        "country": ("美国", "北美高购买力区"),
    },
    {
        "brand": "Elvie",
        "product_line": "吸奶器",
        "platform": "Elvie官网(用户社区)",
        "file": "elvie_babycentre_unlucky.md",
        "url": "https://community.babycentre.co.uk/post/a33711460/elvie-pump-am-i-just-unlucky",
        "country": ("英国", "西欧高信任论坛区"),
    },
]

FETCH_COMMUNITY = [
    {
        "brand": "Baby Brezza",
        "product_line": "喂养电器",
        "platform": "Baby Brezza官网(用户社区)",
        "url": "https://community.whattoexpect.com/forums/formula-feeding/topic/baby-brezza-worth-it-or-waste-of-money-117373815.html",
        "output": "babybrezza_whattoexpect.md",
        "country": ("美国", "北美高购买力区"),
    },
    {
        "brand": "Bugaboo",
        "product_line": "家居出行",
        "platform": "Bugaboo官网(用户社区)",
        "url": "https://www.mumsnet.com/talk/pushchairs_and_prams/4707395-bugaboo-fox-2-issues",
        "output": "bugaboo_mumsnet_issues.md",
        "country": ("英国", "西欧高信任论坛区"),
    },
    {
        "brand": "Willow",
        "product_line": "吸奶器",
        "platform": "Willow官网(用户社区)",
        "url": "https://community.whattoexpect.com/forums/breastfeeding/topic/willow-pump-disappointed-84321615.html",
        "output": "willow_whattoexpect.md",
        "country": ("美国", "北美高购买力区"),
    },
    {
        "brand": "UPPAbaby",
        "product_line": "家居出行",
        "platform": "UPPAbaby官网(用户社区)",
        "url": "https://www.mumsnet.com/talk/pushchairs_and_prams/4887253-uppababy-vista-v2-problems",
        "output": "uppababy_mumsnet.md",
        "country": ("英国", "西欧高信任论坛区"),
    },
]


def extract_user_posts(md: str) -> list[str]:
    """Extract individual user posts/comments from community discussion pages."""
    posts = []
    neg_keywords = [
        "disappoint", "terrible", "awful", "worst", "broken", "defect",
        "waste", "return", "refund", "not recommend", "poor",
        "stopped working", "useless", "horrible", "doesn't work",
        "garbage", "frustrated", "regret", "leak", "broke",
        "noise", "loud", "uncomfortable", "issue", "problem",
        "fault", "malfunction", "bad", "hate",
    ]

    chunks = re.split(r'\n\n+', md)
    for chunk in chunks:
        lower = chunk.lower()
        if not any(kw in lower for kw in neg_keywords):
            continue
        text = re.sub(r'\n', ' ', chunk).strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'Report as Inappropriate', '', text)
        text = text.strip()
        if 25 < len(text) < 500 and not text.startswith("http"):
            posts.append(text[:250])

    seen = set()
    unique = []
    for p in posts:
        key = p[:40].lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


# ---- Phase 3: Additional Trustpilot pages ----

TP_SUPPLEMENTS = [
    {
        "brand": "Elvie",
        "product_line": "吸奶器",
        "platform": "Elvie官网(Trustpilot)",
        "slug": "www.elvie.com",
        "pages": [3, 4, 5],
    },
    {
        "brand": "Willow",
        "product_line": "吸奶器",
        "platform": "Willow官网(Trustpilot)",
        "slug": "willowpump.com",
        "pages": [2, 3],
    },
]


def fetch_trustpilot_page(slug: str, page: int) -> str | None:
    url = f"https://www.trustpilot.com/review/{slug}?page={page}&stars=1&stars=2"
    return fetch_jina(url, f"tp_{slug.replace('.', '_')}_p{page}.md", delay=10.0)


def parse_tp_reviews(md: str) -> list[str]:
    """Extract review texts from Trustpilot markdown."""
    reviews = []
    star_blocks = re.split(r'Rated [12] out of 5', md, flags=re.IGNORECASE)
    if len(star_blocks) > 1:
        for block in star_blocks[1:]:
            text = block[:600].strip()
            text = re.sub(r'\n+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\[.*?\]\(.*?\)', '', text)
            text = re.sub(r'Date of experience.*', '', text)
            text = text.strip()
            if 20 < len(text) < 400:
                reviews.append(text[:250])

    if not reviews:
        sections = re.split(r'\n#{1,4}\s+', md)
        neg_kws = ["disappoint", "terrible", "awful", "broken", "waste", "refund", "horrible"]
        for sec in sections:
            if any(kw in sec.lower() for kw in neg_kws):
                text = re.sub(r'\n+', ' ', sec).strip()[:250]
                if 20 < len(text):
                    reviews.append(text)

    seen = set()
    unique = []
    for r in reviews:
        key = r[:40].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


# ---- Append to CSV ----

def append_rows(rows: list[dict]) -> int:
    existing = set()
    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fns = reader.fieldnames
        for row in reader:
            key = row.get(fns[10], "")[:40].lower()
            existing.add(key)

    new_rows = []
    for r in rows:
        key = r["excerpt"][:40].lower()
        if key not in existing:
            new_rows.append(r)
            existing.add(key)

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

    log(f"[APPEND] {len(new_rows)} new rows to CSV")
    return len(new_rows)


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("", encoding="utf-8")
    log("[START] DTC supplement ingest")

    all_records: list[dict] = []

    # Phase 1: More Momcozy via Okendo
    log("\n===== Phase 1: Momcozy Okendo extra products =====")
    for product_id, product_name, product_line in EXTRA_MOMCOZY_PRODUCTS:
        reviews = fetch_okendo_low(product_id, product_name)
        for text in reviews:
            country, cluster = guess_country(text)
            all_records.append({
                "country": country, "cluster": cluster,
                "product_line": product_line,
                "platform_type": "竞品官方电商",
                "platform": "Momcozy官网",
                "pain": guess_pain(text), "theme": guess_theme(text),
                "excerpt": text, "intensity": guess_intensity(text),
                "brand": "Momcozy",
                "url": f"https://momcozy.com (Okendo: {product_name})",
                "batch": "BATCH-DTC-MOMCOZY-EXTRA-001",
            })
        time.sleep(5)

    log(f"[Phase 1] Momcozy extra: {len(all_records)} records")

    # Phase 2: Community pages (existing + new fetches)
    log("\n===== Phase 2: Community discussions =====")
    phase2_count = 0

    for src in COMMUNITY_SOURCES:
        filepath = RAW_DIR / src["file"]
        if not filepath.exists():
            log(f"  [SKIP] {src['file']} not found")
            continue
        md = filepath.read_text(encoding="utf-8")
        posts = extract_user_posts(md)
        log(f"  [{src['brand']}] {src['file']}: {len(posts)} negative posts")
        for text in posts:
            all_records.append({
                "country": src["country"][0], "cluster": src["country"][1],
                "product_line": src["product_line"],
                "platform_type": "竞品官方电商",
                "platform": src["platform"],
                "pain": guess_pain(text), "theme": guess_theme(text),
                "excerpt": text, "intensity": guess_intensity(text),
                "brand": src["brand"],
                "url": src["url"],
                "batch": f"BATCH-DTC-{src['brand'].upper().replace(' ', '')}-COMMUNITY-001",
            })
            phase2_count += 1

    for src in FETCH_COMMUNITY:
        md = fetch_jina(src["url"], src["output"], delay=10.0)
        if not md:
            continue
        posts = extract_user_posts(md)
        log(f"  [{src['brand']}] {src['output']}: {len(posts)} negative posts")
        for text in posts:
            all_records.append({
                "country": src["country"][0], "cluster": src["country"][1],
                "product_line": src["product_line"],
                "platform_type": "竞品官方电商",
                "platform": src["platform"],
                "pain": guess_pain(text), "theme": guess_theme(text),
                "excerpt": text, "intensity": guess_intensity(text),
                "brand": src["brand"],
                "url": src["url"],
                "batch": f"BATCH-DTC-{src['brand'].upper().replace(' ', '')}-COMMUNITY-001",
            })
            phase2_count += 1

    log(f"[Phase 2] Community: {phase2_count} records")

    # Phase 3: Additional Trustpilot pages
    log("\n===== Phase 3: Trustpilot supplements =====")
    phase3_count = 0
    for tp in TP_SUPPLEMENTS:
        for page in tp["pages"]:
            md = fetch_trustpilot_page(tp["slug"], page)
            if not md:
                continue
            reviews = parse_tp_reviews(md)
            log(f"  [{tp['brand']}] TP page {page}: {len(reviews)} negative reviews")
            for text in reviews:
                country, cluster = guess_country(text)
                all_records.append({
                    "country": country, "cluster": cluster,
                    "product_line": tp["product_line"],
                    "platform_type": "竞品官方电商",
                    "platform": tp["platform"],
                    "pain": guess_pain(text), "theme": guess_theme(text),
                    "excerpt": text, "intensity": guess_intensity(text),
                    "brand": tp["brand"],
                    "url": f"https://www.trustpilot.com/review/{tp['slug']}?page={page}",
                    "batch": f"BATCH-DTC-{tp['brand'].upper()}-TP-SUPP-001",
                })
                phase3_count += 1

    log(f"[Phase 3] Trustpilot: {phase3_count} records")

    # Append
    log(f"\n{'='*60}")
    log(f"[TOTAL] {len(all_records)} DTC supplement records")

    if all_records:
        added = append_rows(all_records)
        log(f"[DONE] Appended {added} new rows to CSV")
    else:
        log("[WARN] No records collected")


if __name__ == "__main__":
    main()
