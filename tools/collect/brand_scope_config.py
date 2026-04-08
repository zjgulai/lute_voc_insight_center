# -*- coding: utf-8 -*-
"""
冻结本轮扩采的竞品品牌范围与入口映射。

来源：当前首页「竞品品牌图谱」所对应的机会点数据快照。
"""
from __future__ import annotations

from typing import Dict, List


# 按首页图谱冻结的扩采品牌名单（按品线）
FROZEN_BRANDS_BY_LINE: Dict[str, List[str]] = {
    "吸奶器": [
        "Elvie",
        "Medela",
        "Spectra",
        "Willow",
        "Momcozy",
        "Lansinoh",
        "Eufy",
        "Baby Buddha",
        "Mumma Bump",
        "Lacteck",
    ],
    "喂养电器": [
        "Tommee Tippee",
        "Philips Avent",
        "Baby Brezza",
        "Chicco",
        "MAM",
        "Dr. Brown's",
        "NUK",
    ],
    "家居出行": [
        "Bugaboo",
        "BabyBjorn",
        "UPPAbaby",
        "Chicco",
        "Graco",
        "Cybex",
        "Joie",
        "Riko",
        "Jané",
        "Peg Perego",
    ],
}


def all_frozen_brands() -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for brands in FROZEN_BRANDS_BY_LINE.values():
        for brand in brands:
            if brand not in seen:
                seen.add(brand)
                out.append(brand)
    return out


# Trustpilot slug 映射（最小可执行）
TRUSTPILOT_SLUGS: Dict[str, str] = {
    "Momcozy": "momcozy.com",
    "Elvie": "elvie.com",
    "Willow": "willowpump.com",
    "Medela": "medela.com",
    "Lansinoh": "lansinoh.com",
    "Spectra": "spectra-baby.com",
    "Tommee Tippee": "tommeetippee.com",
    "Baby Brezza": "babybrezza.com",
    "Bugaboo": "bugaboo.com",
    "UPPAbaby": "uppababy.com",
    "Graco": "gracobaby.com",
    "Cybex": "cybex-online.com",
    "Chicco": "chiccousa.com",
}


# DTC 评论/产品页映射（最小可执行）
DTC_REVIEW_URLS: Dict[str, List[str]] = {
    "Momcozy": [
        "https://momcozy.com/products/momcozy-m5-wearable-breast-pump",
        "https://momcozy.com/products/momcozy-s12-pro-wearable-breast-pump",
        "https://momcozy.com/products/momcozy-m9-wearable-breast-pump",
    ],
    "Elvie": [
        "https://www.elvie.com/en-us/shop/elvie-pump",
        "https://www.elvie.com/en-us/shop/elvie-stride",
    ],
    "Willow": [
        "https://www.willowpump.com/products/willow-go-wearable-breast-pump",
        "https://www.willowpump.com/products/willow-360-wearable-breast-pump",
    ],
    "Medela": [
        "https://www.medela.us/breastfeeding/products/breast-pumps/freestyle-flex",
        "https://www.medela.us/breastfeeding/products/breast-pumps/pump-in-style",
    ],
    "Lansinoh": [
        "https://lansinoh.com/products/smartpump-3-0-double-electric-breast-pump",
    ],
    "Tommee Tippee": [
        "https://www.tommeetippee.com/en-us/product/perfect-prep-machine",
        "https://www.tommeetippee.com/en-us/product/made-for-me-single-electric-breast-pump",
    ],
    "Baby Brezza": [
        "https://www.babybrezza.com/products/formula-pro-advanced",
        "https://www.babybrezza.com/products/bottle-washer-pro",
    ],
    "Bugaboo": [
        "https://www.bugaboo.com/us-en/strollers/bugaboo-fox5/",
        "https://www.bugaboo.com/us-en/strollers/bugaboo-dragonfly/",
    ],
    "UPPAbaby": [
        "https://uppababy.com/vista/",
        "https://uppababy.com/cruz/",
    ],
    "Cybex": [
        "https://www.cybex-online.com/en/us/strollers/",
    ],
    "Graco": [
        "https://www.gracobaby.com/strollers/",
    ],
}


# Reddit/社区已有批量入口文件名到品牌映射（用于 ingest_competitor_zip）
REDDIT_FILENAME_BRAND_HINT: Dict[str, str] = {
    "reddit_elvie_merged.xlsx": "Elvie",
    "reddit_lansinoh_merged.xlsx": "Lansinoh",
    "reddit_willow_merged.xlsx": "Willow",
    "reddit_medela_merged.xlsx": "Medela",
    "reddit_spectra_merged.xlsx": "Spectra",
    "reddit_momcozy_merged.xlsx": "Momcozy",
    "reddit_babybrezza_merged.xlsx": "Baby Brezza",
    "reddit_tommeetippee_merged.xlsx": "Tommee Tippee",
    "reddit_bugaboo_merged.xlsx": "Bugaboo",
    "reddit_uppababy_merged.xlsx": "UPPAbaby",
    "reddit_cybex_merged.xlsx": "Cybex",
    "reddit_graco_merged.xlsx": "Graco",
    "reddit_compare_merged.xlsx": "__compare__",
}
