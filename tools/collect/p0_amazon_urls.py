"""
P0 采集脚本 1/4 — Amazon 负面评论 URL 生成器

功能：
  为 TOP10 国家 × 吸奶器品类生成 Amazon 1-2 星评论的直达 URL 和 Google 定向搜索指令，
  输出可直接用于浏览器打开或半自动爬取。

输出：
  tools/collect/output/p0_amazon_urls.csv
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from urllib.parse import quote_plus

OUTPUT_DIR = Path(__file__).parent / "output"

TOP10_AMAZON = [
    {
        "country": "美国", "code": "US", "cluster": "北美高购买力区",
        "domain": "amazon.com",
        "search_terms": ["breast pump", "wearable breast pump", "electric breast pump"],
        "neg_keywords": ["leak", "painful", "returned", "broken", "stopped working", "not worth", "waste"],
    },
    {
        "country": "加拿大", "code": "CA", "cluster": "北美高购买力区",
        "domain": "amazon.ca",
        "search_terms": ["breast pump", "wearable breast pump", "tire-lait électrique"],
        "neg_keywords": ["leak", "painful", "returned", "broken", "not worth", "fuite", "douleur"],
    },
    {
        "country": "英国", "code": "GB", "cluster": "西欧高信任论坛区",
        "domain": "amazon.co.uk",
        "search_terms": ["breast pump", "wearable breast pump", "electric breast pump"],
        "neg_keywords": ["leak", "painful", "returned", "broken", "noisy", "weak suction"],
    },
    {
        "country": "德国", "code": "DE", "cluster": "西欧高信任论坛区",
        "domain": "amazon.de",
        "search_terms": ["milchpumpe", "elektrische milchpumpe", "tragbare milchpumpe"],
        "neg_keywords": ["schmerzen", "auslaufen", "laut", "defekt", "enttäuschend", "zurückgeschickt"],
    },
    {
        "country": "法国", "code": "FR", "cluster": "西欧高信任论坛区",
        "domain": "amazon.fr",
        "search_terms": ["tire-lait", "tire lait électrique", "tire-lait portable"],
        "neg_keywords": ["douleur", "fuite", "bruit", "décevant", "retourné", "cassé"],
    },
    {
        "country": "西班牙", "code": "ES", "cluster": "西欧高信任论坛区",
        "domain": "amazon.es",
        "search_terms": ["sacaleches", "extractor de leche", "sacaleches eléctrico"],
        "neg_keywords": ["dolor", "fuga", "ruidoso", "decepcionante", "devuelto", "roto"],
    },
    {
        "country": "墨西哥", "code": "MX", "cluster": "拉美社媒口碑区",
        "domain": "amazon.com.mx",
        "search_terms": ["sacaleches", "extractor de leche", "extractor eléctrico"],
        "neg_keywords": ["dolor", "fuga", "ruidoso", "malo", "no funciona", "decepcionante"],
    },
    {
        "country": "阿联酋", "code": "AE", "cluster": "中东视觉社媒区",
        "domain": "amazon.ae",
        "search_terms": ["breast pump", "wearable breast pump", "electric breast pump"],
        "neg_keywords": ["leak", "painful", "noisy", "stopped working", "waste of money"],
    },
    {
        "country": "澳大利亚", "code": "AU", "cluster": "英语成熟市场",
        "domain": "amazon.com.au",
        "search_terms": ["breast pump", "wearable breast pump", "electric breast pump"],
        "neg_keywords": ["leak", "painful", "returned", "broken", "noisy", "weak suction"],
    },
    {
        "country": "沙特阿拉伯", "code": "SA", "cluster": "中东视觉社媒区",
        "domain": "amazon.sa",
        "search_terms": ["breast pump", "wearable breast pump", "شفاط حليب"],
        "neg_keywords": ["leak", "painful", "noisy", "stopped working", "waste"],
    },
]


def build_amazon_search_url(domain: str, term: str) -> str:
    """Amazon 搜索链接（品类搜索入口，人工再按星级筛选）"""
    return f"https://www.{domain}/s?k={quote_plus(term)}"


def build_amazon_review_filter_url(domain: str, term: str) -> str:
    """Amazon 搜索 + 用户评级 1-2 星筛选参数"""
    return f"https://www.{domain}/s?k={quote_plus(term)}&rh=p_72%3A1-2"


def build_google_site_query(domain: str, term: str, neg_kw: str) -> str:
    """Google site:amazon.xx 定向搜索负面评论"""
    return f'site:{domain} "{term}" ({neg_kw})'


def build_google_search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "p0_amazon_urls.csv"

    fieldnames = [
        "国家", "国家编码", "区域cluster", "Amazon域名",
        "搜索词", "搜索词(本地语言)",
        "Amazon搜索URL", "Amazon1-2星URL",
        "Google定向查询", "Google搜索URL",
        "负面关键词包", "批次编码",
    ]

    rows = []
    for c in TOP10_AMAZON:
        for i, term in enumerate(c["search_terms"]):
            neg_kw_str = " OR ".join(f'"{w}"' for w in c["neg_keywords"][:4])
            google_q = build_google_site_query(c["domain"], term, neg_kw_str)
            batch = f"BATCH-P0-{c['code']}-{i+1:03d}"

            rows.append({
                "国家": c["country"],
                "国家编码": c["code"],
                "区域cluster": c["cluster"],
                "Amazon域名": c["domain"],
                "搜索词": term,
                "搜索词(本地语言)": term,
                "Amazon搜索URL": build_amazon_search_url(c["domain"], term),
                "Amazon1-2星URL": build_amazon_review_filter_url(c["domain"], term),
                "Google定向查询": google_q,
                "Google搜索URL": build_google_search_url(google_q),
                "负面关键词包": ";".join(c["neg_keywords"]),
                "批次编码": batch,
            })

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[P0 URL 生成器] 共生成 {len(rows)} 条采集 URL → {output_path}")
    print(f"  覆盖 {len(TOP10_AMAZON)} 个国家 × {len(rows)//len(TOP10_AMAZON)} 个搜索词/国")
    return rows


if __name__ == "__main__":
    main()
