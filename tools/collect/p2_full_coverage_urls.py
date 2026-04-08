"""
P2 采集脚本 — TOP20 × 其余品线 × 可访问平台 + 竞品独立站评论

范围：
  A) TOP20 × 家居出行 / 内衣服饰 / 智能母婴电器 × Amazon + 社区
  B) TOP20 × 所有品线 × 竞品独立站第三方评测聚合（Trustpilot / 独立测评站）
  C) TOP10 × 所有品线 × 竞品官方社媒（Instagram / Facebook 品牌页）

输出：
  tools/collect/output/p2_full_coverage_urls.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import quote_plus

from competitor_registry import (
    AMAZON_DOMAINS, COMPETITOR_BRANDS,
    TOP10_COUNTRIES, TOP20_COUNTRIES,
    get_brands_by_line, get_brands_by_line_and_region,
    get_dtc_domain_for_country,
)

OUTPUT_DIR = Path(__file__).parent / "output"

P2_LINES = ["家居出行", "内衣服饰", "智能母婴电器"]

LINE_SEARCH_TERMS = {
    "家居出行": {
        "US": ["stroller review problem", "baby carrier uncomfortable", "car seat complaint"],
        "CA": ["stroller review problem", "poussette avis négatif"],
        "GB": ["pushchair review problem", "pram complaint", "baby carrier issue"],
        "DE": ["kinderwagen test problem", "babytrage erfahrung negativ"],
        "FR": ["poussette avis négatif", "porte-bébé problème"],
        "ES": ["cochecito reseña negativa", "portabebé problema"],
        "MX": ["carriola reseña negativa", "portabebé opiniones"],
        "AE": ["stroller review problem", "عربة أطفال مشكلة"],
        "AU": ["pram review problem", "stroller complaint Australia"],
        "SA": ["stroller review problem", "عربة أطفال"],
    },
    "内衣服饰": {
        "US": ["nursing bra review", "maternity underwear uncomfortable", "postpartum shapewear complaint"],
        "GB": ["nursing bra review problem", "maternity wear complaint"],
        "DE": ["still-bh test problem", "umstandsmode erfahrung"],
        "FR": ["soutien-gorge allaitement avis", "sous-vêtements grossesse"],
    },
    "智能母婴电器": {
        "US": ["baby monitor review problem", "smart baby gadget complaint", "baby camera issue"],
        "GB": ["baby monitor review problem", "smart nursery issue"],
        "DE": ["babyphone test problem", "baby monitor erfahrung"],
        "FR": ["babyphone avis négatif", "écoute-bébé problème"],
    },
}

THIRD_PARTY_REVIEW_SITES = [
    {"name": "Trustpilot", "domain": "trustpilot.com", "url_tpl": "https://www.trustpilot.com/review/{brand_domain}"},
    {"name": "Wirecutter", "domain": "nytimes.com/wirecutter", "search_tpl": 'site:nytimes.com/wirecutter "{brand}" review'},
    {"name": "BabyGearLab", "domain": "babygearlab.com", "search_tpl": 'site:babygearlab.com "{brand}" review'},
    {"name": "Which?", "domain": "which.co.uk", "search_tpl": 'site:which.co.uk "{brand}" review'},
    {"name": "Stiftung Warentest", "domain": "test.de", "search_tpl": 'site:test.de "{brand}" test'},
    {"name": "Les Numériques", "domain": "lesnumeriques.com", "search_tpl": 'site:lesnumeriques.com "{brand}" test'},
    {"name": "OCU", "domain": "ocu.org", "search_tpl": 'site:ocu.org "{brand}" análisis'},
]

BRAND_SOCIAL_PLATFORMS = [
    {"name": "Instagram", "url_tpl": "https://www.instagram.com/{handle}/", "search_tpl": "https://www.instagram.com/explore/tags/{hashtag}/"},
    {"name": "Facebook", "url_tpl": "https://www.facebook.com/{handle}/reviews"},
]


def gen_amazon_coverage():
    rows = []
    for c in TOP20_COUNTRIES:
        code = c["code"]
        amazon = AMAZON_DOMAINS.get(code, "")
        if not amazon:
            continue
        for line in P2_LINES:
            terms = LINE_SEARCH_TERMS.get(line, {}).get(code, [])
            if not terms:
                generic = LINE_SEARCH_TERMS.get(line, {}).get("US", [f"{line} review"])
                terms = generic[:1]
            for term in terms:
                rows.append({
                    "阶段": "P2-A", "国家": c["country"], "国家编码": code,
                    "产品品线": line, "平台类型": "电商评论类",
                    "平台": f"Amazon ({amazon})",
                    "搜索词": term,
                    "URL": f"https://www.{amazon}/s?k={quote_plus(term)}&rh=p_72%3A1-2",
                    "批次编码": f"BATCH-P2A-{code}",
                })
    return rows


def gen_third_party_reviews():
    rows = []
    for brand in COMPETITOR_BRANDS:
        dtc = brand["dtc_domain"]
        for site in THIRD_PARTY_REVIEW_SITES:
            if "url_tpl" in site and "{brand_domain}" in site.get("url_tpl", ""):
                url = site["url_tpl"].format(brand_domain=dtc)
                rows.append({
                    "阶段": "P2-B", "国家": "全球", "国家编码": "GLOBAL",
                    "产品品线": brand["product_line"], "平台类型": "第三方评测",
                    "平台": f"{site['name']} → {brand['brand']}",
                    "搜索词": brand["brand"],
                    "URL": url,
                    "批次编码": f"BATCH-P2B-{brand['brand'].replace(' ', '')}",
                })

            if "search_tpl" in site:
                query = site["search_tpl"].format(brand=brand["brand"])
                rows.append({
                    "阶段": "P2-B", "国家": "全球", "国家编码": "GLOBAL",
                    "产品品线": brand["product_line"], "平台类型": "第三方评测Google",
                    "平台": f"Google → {site['name']}",
                    "搜索词": f"{brand['brand']} on {site['name']}",
                    "URL": f"https://www.google.com/search?q={quote_plus(query)}",
                    "批次编码": f"BATCH-P2B-{brand['brand'].replace(' ', '')}",
                })
    return rows


def gen_brand_social():
    rows = []
    for brand in COMPETITOR_BRANDS:
        handle = brand["brand"].lower().replace(" ", "").replace(".", "").replace("'", "")
        hashtag = brand["brand"].lower().replace(" ", "").replace(".", "").replace("'", "")

        rows.append({
            "阶段": "P2-C", "国家": "全球", "国家编码": "GLOBAL",
            "产品品线": brand["product_line"], "平台类型": "竞品官方社媒",
            "平台": f"Instagram @{handle}",
            "搜索词": f"#{hashtag} reviews complaints",
            "URL": f"https://www.instagram.com/explore/tags/{hashtag}review/",
            "批次编码": f"BATCH-P2C-{brand['brand'].replace(' ', '')}",
        })

        rows.append({
            "阶段": "P2-C", "国家": "全球", "国家编码": "GLOBAL",
            "产品品线": brand["product_line"], "平台类型": "竞品官方社媒",
            "平台": f"Facebook {brand['brand']} Reviews",
            "搜索词": f"{brand['brand']} review complaint",
            "URL": f"https://www.facebook.com/search/posts/?q={quote_plus(brand['brand'] + ' review problem')}",
            "批次编码": f"BATCH-P2C-{brand['brand'].replace(' ', '')}",
        })
    return rows


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []

    amazon_rows = gen_amazon_coverage()
    all_rows.extend(amazon_rows)
    print(f"  P2-A Amazon 覆盖: {len(amazon_rows)} 条")

    tp_rows = gen_third_party_reviews()
    all_rows.extend(tp_rows)
    print(f"  P2-B 第三方评测: {len(tp_rows)} 条")

    social_rows = gen_brand_social()
    all_rows.extend(social_rows)
    print(f"  P2-C 竞品社媒: {len(social_rows)} 条")

    output_path = OUTPUT_DIR / "p2_full_coverage_urls.csv"
    fields = ["阶段", "国家", "国家编码", "产品品线", "平台类型", "平台", "搜索词", "URL", "批次编码"]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k, "") for k in fields})

    print(f"\n[P2 全覆盖] 共 {len(all_rows)} 条 → {output_path}")

    phase_counts = {}
    for r in all_rows:
        p = r["阶段"]
        phase_counts[p] = phase_counts.get(p, 0) + 1
    for p, cnt in sorted(phase_counts.items()):
        print(f"  {p}: {cnt} 条")

    return len(all_rows)


if __name__ == "__main__":
    main()
