"""
Collect negative reviews from competitor DTC sites via their review APIs.
- Momcozy: Okendo API (paginated, filter by rating <= 3)
- Others: Google search for indexed negative reviews, then fetch via r.jina.ai
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
RAW_DIR = OUTPUT_DIR / "raw_dtc"
RAW_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUTPUT_DIR / "dtc_api_ingest_log.txt"

HEADERS_20 = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期",
    "痛点大类(功能/价格/体验/服务/安全)", "负面主题",
    "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌",
    "对应运营建议", "来源URL", "采集日期", "批次编码", "优先级",
]

PAIN_KEYWORDS = {
    "功能": ["stopped working", "broken", "defect", "malfunction", "motor", "battery",
             "pump", "suction", "not work", "died", "broke", "fail", "doesn't work",
             "won't turn on", "quit", "stopped", "dead"],
    "价格": ["expensive", "price", "cost", "overpriced", "waste of money", "rip off",
             "not worth", "too much"],
    "体验": ["leak", "size", "fit", "loud", "noise", "difficult", "complicated",
             "messy", "hard to clean", "bulky", "uncomfortable", "heavy", "painful",
             "hurt", "small", "large", "awkward"],
    "服务": ["customer service", "support", "warranty", "return", "refund",
             "shipping", "delivery", "replace", "response", "exchange", "unhelpful"],
    "安全": ["injury", "burn", "hot", "unsafe", "recall", "BPA", "chemical", "mold"],
}

INTENSITY_RULES = {
    "高": ["terrible", "awful", "worst", "never", "do not buy", "waste", "dangerous",
           "useless", "garbage", "scam", "horrible", "zero stars", "disgusting",
           "regret", "hate"],
    "中": ["disappointed", "frustrated", "poor", "bad", "not recommend", "mediocre",
           "annoying", "issue", "problem"],
    "低": ["okay", "could be better", "minor", "decent but", "not great"],
}

THEME_RULES = [
    ("产品耐久性差", ["broke", "fail", "stopped working", "last", "defect", "worn out", "died", "quit"]),
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


def log(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    try:
        print(msg, flush=True)
    except Exception:
        pass


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
    if any(w in t for w in ["uk", "nhs", "boots"]):
        return ("英国", "西欧高信任论坛区")
    if any(w in t for w in ["canada", "canadian"]):
        return ("加拿大", "北美高购买力区")
    if any(w in t for w in ["australia", "aud"]):
        return ("澳大利亚", "英联邦信任区")
    return ("美国", "北美高购买力区")


# ---- Okendo API for Momcozy ----

OKENDO_STORE_ID = "fd7a9ef8-afae-47de-a7c1-4ca9730e4d32"

MOMCOZY_PRODUCTS = [
    ("shopify-8002089779398", "M5 Wearable Breast Pump"),
    ("shopify-7918308491462", "M6 Mobile Breast Pump"),
    ("shopify-8469876015302", "Air 1 Ultra-slim Breast Pump"),
    ("shopify-8435496550598", "BM04 Baby Monitor"),
]


def fetch_okendo_reviews(product_id: str, product_name: str, max_pages: int = 10) -> list[dict]:
    """Paginate through Okendo reviews for a Momcozy product, collecting low-rated ones."""
    reviews = []
    base_url = f"https://api.okendo.io/v1/stores/{OKENDO_STORE_ID}/products/{product_id}/reviews"
    next_url = f"{base_url}?limit=50&orderBy=rating%20asc"

    for page in range(max_pages):
        log(f"  [OKENDO] {product_name} page {page+1} ...")
        try:
            req = urllib.request.Request(next_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            log(f"    [WARN] Fetch failed: {e}")
            break

        page_reviews = data.get("reviews", [])
        if not page_reviews:
            log(f"    [END] No more reviews")
            break

        for r in page_reviews:
            rating = r.get("rating", 5)
            if rating <= 3:
                body = r.get("body", "")
                title = r.get("title", "")
                text = f"{title}. {body}" if title else body
                if len(text) > 20:
                    reviews.append({
                        "text": text[:300],
                        "rating": rating,
                        "product": product_name,
                    })

        log(f"    [PAGE] {len(page_reviews)} reviews, {len(reviews)} negative so far")

        next_url_path = data.get("nextUrl", "")
        if not next_url_path:
            break
        if next_url_path.startswith("http"):
            next_url = next_url_path
        else:
            next_url = f"https://api.okendo.io{next_url_path}"

        time.sleep(3)

    log(f"  [OKENDO] {product_name}: {len(reviews)} negative reviews found")
    return reviews


def collect_momcozy_okendo() -> list[dict]:
    """Collect negative reviews from Momcozy via Okendo API."""
    log("\n[BRAND] Momcozy (Okendo API)")
    all_records = []

    for product_id, product_name in MOMCOZY_PRODUCTS:
        reviews = fetch_okendo_reviews(product_id, product_name)
        for rev in reviews:
            country, cluster = guess_country(rev["text"])
            all_records.append({
                "country": country,
                "cluster": cluster,
                "product_line": "吸奶器" if "Pump" in product_name else "智能监控",
                "platform_type": "竞品官方电商",
                "platform": "Momcozy官网",
                "pain": guess_pain(rev["text"]),
                "theme": guess_theme(rev["text"]),
                "excerpt": rev["text"],
                "intensity": guess_intensity(rev["text"]),
                "brand": "Momcozy",
                "url": f"https://momcozy.com (Okendo: {product_name})",
                "batch": "BATCH-DTC-MOMCOZY-API-001",
            })
        time.sleep(5)

    log(f"  [TOTAL] Momcozy: {len(all_records)} negative records")
    return all_records


# ---- Google search for other brands ----

GOOGLE_QUERIES = [
    {
        "brand": "Elvie",
        "product_line": "吸奶器",
        "platform": "Elvie官网",
        "queries": [
            "Elvie pump review disappointed OR broken OR refund OR terrible site:elvie.com OR site:trustpilot.com/review/elvie.com",
        ],
    },
    {
        "brand": "Baby Brezza",
        "product_line": "喂养电器",
        "platform": "Baby Brezza官网",
        "queries": [
            "Baby Brezza formula pro review disappointed OR broken OR defective site:babybrezza.com",
        ],
    },
    {
        "brand": "Bugaboo",
        "product_line": "家居出行",
        "platform": "Bugaboo官网",
        "queries": [
            "Bugaboo stroller review disappointed OR broken OR quality issue site:bugaboo.com",
        ],
    },
]


def search_and_extract(config: dict) -> list[dict]:
    """Use r.jina.ai to search Google for brand-specific DTC negative reviews."""
    brand = config["brand"]
    product_line = config["product_line"]
    platform = config["platform"]
    records = []

    log(f"\n[BRAND] {brand} (Google search)")

    for query in config["queries"]:
        encoded = urllib.parse.quote(query)
        google_url = f"https://www.google.com/search?q={encoded}&num=10"
        jina_url = f"https://r.jina.ai/{google_url}"

        log(f"  [SEARCH] {query[:60]}...")

        try:
            req = urllib.request.Request(jina_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                md = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            log(f"    [WARN] Search failed: {e}")
            time.sleep(10)
            continue

        raw_path = RAW_DIR / f"{brand.replace(' ', '_')}_google_search.md"
        raw_path.write_text(md, encoding="utf-8")
        log(f"    [SAVE] {raw_path.name} ({len(md)} bytes)")

        neg_keywords = [
            "disappoint", "terrible", "awful", "worst", "broken", "defect",
            "waste", "refund", "not recommend", "poor quality", "stopped working",
            "useless", "horrible", "doesn't work", "frustrated",
        ]

        sections = re.split(r'\n(?:#{1,4}\s+)', md)
        for section in sections:
            lower = section.lower()
            if any(kw in lower for kw in neg_keywords):
                text = re.sub(r'\n+', ' ', section).strip()
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'\[.*?\]\(.*?\)', '', text)
                text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
                if 30 < len(text) < 500:
                    country, cluster = guess_country(text)
                    records.append({
                        "country": country,
                        "cluster": cluster,
                        "product_line": product_line,
                        "platform_type": "竞品官方电商",
                        "platform": platform,
                        "pain": guess_pain(text),
                        "theme": guess_theme(text),
                        "excerpt": text[:200],
                        "intensity": guess_intensity(text),
                        "brand": brand,
                        "url": f"https://www.google.com/search?q={encoded}",
                        "batch": f"BATCH-DTC-{brand.upper().replace(' ', '')}-GOOGLE-001",
                    })

        time.sleep(10)

    log(f"  [TOTAL] {brand}: {len(records)} negative records from Google")
    return records


# ---- Dedup and append ----

def append_rows(rows: list[dict]) -> int:
    existing = set()
    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fns = reader.fieldnames
        for row in reader:
            key = row.get(fns[10], "")[:50]
            existing.add(key)

    new_rows = []
    for r in rows:
        key = r["excerpt"][:50]
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
    log("[START] DTC API batch ingest")

    all_records = []

    momcozy = collect_momcozy_okendo()
    all_records.extend(momcozy)

    for config in GOOGLE_QUERIES:
        records = search_and_extract(config)
        all_records.extend(records)

    log(f"\n{'='*60}")
    log(f"[TOTAL] Collected {len(all_records)} DTC negative review records")

    if all_records:
        added = append_rows(all_records)
        log(f"[DONE] Appended {added} new rows to CSV")
    else:
        log("[WARN] No DTC reviews collected")


if __name__ == "__main__":
    main()
