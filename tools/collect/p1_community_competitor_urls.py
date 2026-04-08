"""
P1 采集脚本 — 社区论坛 + YouTube + 竞品独立站/官方电商 URL 生成器

范围：
  A) TOP10 × 喂养电器 × Amazon + 社区论坛 + YouTube
  B) TOP11-20 × 吸奶器 × 社区论坛 + YouTube
  C) TOP10 × 吸奶器+喂养电器 × 竞品独立站评论 + 竞品 Amazon 品牌筛选
  D) TOP10 × 家居出行 × 竞品独立站评论

输出：
  tools/collect/output/p1_community_urls.csv
  tools/collect/output/p1_competitor_dtc_urls.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import quote_plus

from competitor_registry import (
    AMAZON_DOMAINS,
    TOP10_COUNTRIES, TOP11_20_COUNTRIES,
    get_brands_by_line_and_region, get_dtc_domain_for_country,
)

OUTPUT_DIR = Path(__file__).parent / "output"


# ━━━━━━━━━━━━━ 社区论坛 + YouTube ━━━━━━━━━━━━━

COMMUNITY_PLATFORMS = {
    "US": [
        {"platform": "Reddit", "type": "垂类社区类", "url_tpl": "https://www.reddit.com/r/{sub}/search/?q={q}", "subs": ["breastfeeding", "BabyBumps", "BeyondTheBump", "FormulaFeeders"]},
        {"platform": "What to Expect", "type": "垂类社区类", "url_tpl": "https://community.whattoexpect.com/search?q={q}"},
        {"platform": "YouTube", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "CA": [
        {"platform": "Reddit", "type": "垂类社区类", "url_tpl": "https://www.reddit.com/r/{sub}/search/?q={q}", "subs": ["BabyBumpsCanada"]},
        {"platform": "BabyCenter Canada", "type": "垂类社区类", "url_tpl": "https://community.babycenter.com/search?q={q}"},
        {"platform": "YouTube", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "GB": [
        {"platform": "Mumsnet", "type": "垂类社区类", "url_tpl": "https://www.mumsnet.com/search?q={q}"},
        {"platform": "Netmums Forum", "type": "垂类社区类", "url_tpl": "https://www.netmums.com/search?q={q}"},
        {"platform": "YouTube", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "DE": [
        {"platform": "urbia", "type": "垂类社区类", "url_tpl": "https://www.urbia.de/suche?q={q}"},
        {"platform": "Rund-ums-Baby", "type": "垂类社区类", "url_tpl": "https://www.rund-ums-baby.de/suche/?q={q}"},
        {"platform": "YouTube DE", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "FR": [
        {"platform": "Doctissimo Forum", "type": "垂类社区类", "url_tpl": "https://forum.doctissimo.fr/search?q={q}"},
        {"platform": "Magicmaman Forum", "type": "垂类社区类", "url_tpl": "https://forum.magicmaman.com/search?q={q}"},
        {"platform": "YouTube FR", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "ES": [
        {"platform": "enfemenino", "type": "垂类社区类", "url_tpl": "https://www.enfemenino.com/search?q={q}"},
        {"platform": "YouTube ES", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "MX": [
        {"platform": "BabyCenter Español", "type": "垂类社区类", "url_tpl": "https://espanol.babycenter.com/search?q={q}"},
        {"platform": "YouTube MX", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "AE": [
        {"platform": "ExpatWoman UAE", "type": "垂类社区类", "url_tpl": "https://www.expatwoman.com/search?q={q}"},
        {"platform": "YouTube AE", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "AU": [
        {"platform": "Facebook Groups", "type": "垂类社区类", "url_tpl": "https://www.facebook.com/search/groups/?q={q}"},
        {"platform": "YouTube AU", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
    "SA": [
        {"platform": "BabyCenter Community", "type": "垂类社区类", "url_tpl": "https://community.babycenter.com/search?q={q}"},
        {"platform": "YouTube SA", "type": "社媒传播类", "url_tpl": "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"},
    ],
}

FEEDING_SEARCH_TERMS = {
    "US": ["bottle warmer review", "sterilizer problem", "baby food maker issue"],
    "CA": ["bottle warmer review", "chauffe-biberon avis"],
    "GB": ["bottle warmer review", "steriliser problem"],
    "DE": ["flaschenwärmer test", "sterilisator problem"],
    "FR": ["chauffe-biberon avis", "stérilisateur problème"],
    "ES": ["calienta biberones reseña", "esterilizador problema"],
    "MX": ["calienta biberones reseña", "esterilizador opiniones"],
    "AE": ["bottle warmer review", "مسخن رضاعة مشكلة"],
    "AU": ["bottle warmer review", "steriliser issue"],
    "SA": ["bottle warmer review", "مسخن رضاعة"],
}

PUMP_SEARCH_TERMS_EXTENDED = {
    "CN": ["吸奶器 差评", "吸奶器 不好用", "吸奶器 问题"],
    "IT": ["tiralatte recensione negativa", "tiralatte problema"],
    "MY": ["breast pump review problem", "breast pump Malaysia"],
    "AT": ["milchpumpe test problem", "milchpumpe erfahrung"],
    "VN": ["máy hút sữa đánh giá", "máy hút sữa vấn đề"],
    "PL": ["laktator opinia negatywna", "laktator problem"],
    "PH": ["breast pump review Philippines", "breast pump problem"],
    "TH": ["เครื่องปั๊มนม รีวิว ปัญหา", "breast pump review Thailand"],
    "NL": ["borstkolf review probleem", "borstkolf ervaring"],
    "BE": ["tire-lait avis problème", "borstkolf ervaring"],
}


def gen_community_urls() -> list[dict]:
    """生成社区 + YouTube 采集 URL"""
    rows = []

    for c in TOP10_COUNTRIES:
        code = c["code"]
        platforms = COMMUNITY_PLATFORMS.get(code, [])
        terms = FEEDING_SEARCH_TERMS.get(code, ["bottle warmer review"])
        for plat in platforms:
            for term in terms:
                q = quote_plus(term)
                if "subs" in plat:
                    for sub in plat["subs"]:
                        url = plat["url_tpl"].format(sub=sub, q=q)
                        rows.append({
                            "阶段": "P1-A", "国家": c["country"], "国家编码": code,
                            "产品品线": "喂养电器", "平台类型": plat["type"],
                            "平台": f"{plat['platform']} r/{sub}", "搜索词": term,
                            "URL": url, "批次编码": f"BATCH-P1A-{code}",
                        })
                else:
                    url = plat["url_tpl"].format(q=q)
                    rows.append({
                        "阶段": "P1-A", "国家": c["country"], "国家编码": code,
                        "产品品线": "喂养电器", "平台类型": plat["type"],
                        "平台": plat["platform"], "搜索词": term,
                        "URL": url, "批次编码": f"BATCH-P1A-{code}",
                    })

    for c in TOP11_20_COUNTRIES:
        code = c["code"]
        terms = PUMP_SEARCH_TERMS_EXTENDED.get(code, ["breast pump review problem"])
        yt_url_tpl = "https://www.youtube.com/results?search_query={q}&sp=CAMSBAgEEAE%253D"
        google_tpl = "https://www.google.com/search?q={q}"
        for term in terms:
            q = quote_plus(term)
            rows.append({
                "阶段": "P1-B", "国家": c["country"], "国家编码": code,
                "产品品线": "吸奶器", "平台类型": "社媒传播类",
                "平台": "YouTube", "搜索词": term,
                "URL": yt_url_tpl.format(q=q), "批次编码": f"BATCH-P1B-{code}",
            })
            rows.append({
                "阶段": "P1-B", "国家": c["country"], "国家编码": code,
                "产品品线": "吸奶器", "平台类型": "搜索引擎",
                "平台": "Google", "搜索词": term,
                "URL": google_tpl.format(q=q), "批次编码": f"BATCH-P1B-{code}",
            })

    return rows


# ━━━━━━━━━━━━━ 竞品独立站 / 官方电商 ━━━━━━━━━━━━━

def gen_competitor_dtc_urls() -> list[dict]:
    """生成竞品 DTC 独立站 + Amazon 品牌筛选 URL"""
    rows = []

    for c in TOP10_COUNTRIES:
        code = c["code"]

        for line in ["吸奶器", "喂养电器", "家居出行"]:
            brands = get_brands_by_line_and_region(line, code)
            amazon_domain = AMAZON_DOMAINS.get(code, "")

            for brand in brands:
                dtc_domain = get_dtc_domain_for_country(brand, code)
                dtc_review_url = brand["dtc_review_url"]

                rows.append({
                    "阶段": "P1-C", "国家": c["country"], "国家编码": code,
                    "产品品线": line, "平台类型": "竞品独立站",
                    "平台": f"{brand['brand']} DTC ({dtc_domain})",
                    "搜索词": ", ".join(brand["key_models"][:3]),
                    "URL": dtc_review_url,
                    "Google定向查询": brand["google_review_query"],
                    "Google搜索URL": f"https://www.google.com/search?q={quote_plus(brand['google_review_query'])}",
                    "批次编码": f"BATCH-P1C-{code}-{brand['brand'].replace(' ', '')}",
                })

                if amazon_domain:
                    for model in brand["key_models"][:2]:
                        amazon_url = f"https://www.{amazon_domain}/s?k={quote_plus(model)}&rh=p_72%3A1-2"
                        rows.append({
                            "阶段": "P1-C", "国家": c["country"], "国家编码": code,
                            "产品品线": line, "平台类型": "竞品Amazon评论",
                            "平台": f"Amazon ({amazon_domain})",
                            "搜索词": model,
                            "URL": amazon_url,
                            "Google定向查询": f'site:{amazon_domain} "{model}" ("1 star" OR "terrible" OR "not worth")',
                            "Google搜索URL": f"https://www.google.com/search?q={quote_plus(f'site:{amazon_domain} \"{model}\" review problem')}",
                            "批次编码": f"BATCH-P1C-{code}-{brand['brand'].replace(' ', '')}",
                        })

                site_q = f'site:{dtc_domain} "review" ("problem" OR "disappointed" OR "returned")'
                rows.append({
                    "阶段": "P1-C", "国家": c["country"], "国家编码": code,
                    "产品品线": line, "平台类型": "竞品独立站Google定向",
                    "平台": f"Google → {dtc_domain}",
                    "搜索词": f"{brand['brand']} negative reviews",
                    "URL": f"https://www.google.com/search?q={quote_plus(site_q)}",
                    "Google定向查询": site_q,
                    "Google搜索URL": f"https://www.google.com/search?q={quote_plus(site_q)}",
                    "批次编码": f"BATCH-P1C-{code}-{brand['brand'].replace(' ', '')}",
                })

    return rows


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    community_rows = gen_community_urls()
    community_path = OUTPUT_DIR / "p1_community_urls.csv"
    fields_c = ["阶段", "国家", "国家编码", "产品品线", "平台类型", "平台", "搜索词", "URL", "批次编码"]
    with open(community_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields_c)
        w.writeheader()
        w.writerows(community_rows)
    print(f"[P1 社区+YouTube] {len(community_rows)} 条 → {community_path}")

    dtc_rows = gen_competitor_dtc_urls()
    dtc_path = OUTPUT_DIR / "p1_competitor_dtc_urls.csv"
    fields_d = ["阶段", "国家", "国家编码", "产品品线", "平台类型", "平台", "搜索词", "URL", "Google定向查询", "Google搜索URL", "批次编码"]
    with open(dtc_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields_d)
        w.writeheader()
        w.writerows(dtc_rows)
    print(f"[P1 竞品独立站] {len(dtc_rows)} 条 → {dtc_path}")

    line_counts = {}
    for r in dtc_rows:
        key = f"{r['产品品线']}|{r['平台类型']}"
        line_counts[key] = line_counts.get(key, 0) + 1
    print("\n  品线×类型 分布:")
    for k, v in sorted(line_counts.items()):
        print(f"    {k}: {v} 条")

    return len(community_rows) + len(dtc_rows)


if __name__ == "__main__":
    main()
