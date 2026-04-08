"""
竞品品牌独立站 & 官方电商注册表（全品线共用）

所有采集脚本通过本文件获取竞品品牌信息，包括：
  - 品牌名称 / DTC 独立站域名
  - 评论页 URL 模板
  - 品线归属
  - Google 定向搜索模板
  - 各国本地化电商平台映射
"""

from __future__ import annotations

COMPETITOR_BRANDS: list[dict] = [
    # ── 吸奶器 ──
    {
        "brand": "Spectra",
        "product_line": "吸奶器",
        "dtc_domain": "spectra-baby.com",
        "dtc_review_url": "https://www.spectra-baby.com/collections/breast-pumps",
        "dtc_regions": ["US", "GB", "AU", "CA"],
        "google_review_query": 'site:spectra-baby.com "review" ("1 star" OR "disappointed" OR "not worth")',
        "amazon_brand_filter": "Spectra",
        "key_models": ["Spectra S1", "Spectra S2", "Spectra S2 Plus", "Spectra Synergy Gold"],
    },
    {
        "brand": "Medela",
        "product_line": "吸奶器",
        "dtc_domain": "medela.com",
        "dtc_review_url": "https://www.medela.com/breastfeeding/products/breast-pumps",
        "dtc_regions": ["US", "GB", "DE", "FR", "ES", "AU", "CA"],
        "google_review_query": 'site:medela.com "review" ("disappointed" OR "problem" OR "issue")',
        "amazon_brand_filter": "Medela",
        "key_models": ["Medela Pump in Style", "Medela Swing Maxi", "Medela Freestyle Flex", "Medela Harmony"],
        "local_domains": {
            "DE": "medela.de", "FR": "medela.fr", "ES": "medela.es",
            "GB": "medela.co.uk", "AU": "medela.com.au", "CA": "medela.ca",
        },
    },
    {
        "brand": "Elvie",
        "product_line": "吸奶器",
        "dtc_domain": "elvie.com",
        "dtc_review_url": "https://www.elvie.com/shop/elvie-pump",
        "dtc_regions": ["US", "GB", "DE", "FR"],
        "google_review_query": 'site:elvie.com "review" ("battery" OR "suction" OR "disappointed")',
        "amazon_brand_filter": "Elvie",
        "key_models": ["Elvie Pump", "Elvie Stride"],
    },
    {
        "brand": "Willow",
        "product_line": "吸奶器",
        "dtc_domain": "willowpump.com",
        "dtc_review_url": "https://www.willowpump.com/products",
        "dtc_regions": ["US"],
        "google_review_query": 'site:willowpump.com "review" ("leak" OR "expensive" OR "not worth")',
        "amazon_brand_filter": "Willow",
        "key_models": ["Willow Go", "Willow 3.0"],
    },
    {
        "brand": "Momcozy",
        "product_line": "吸奶器",
        "dtc_domain": "momcozy.com",
        "dtc_review_url": "https://momcozy.com/collections/wearable-breast-pumps",
        "dtc_regions": ["US", "GB", "DE", "FR", "AU", "CA", "AE", "SA"],
        "google_review_query": 'site:momcozy.com "review" ("suction" OR "leak" OR "noise" OR "not worth")',
        "amazon_brand_filter": "Momcozy",
        "key_models": ["Momcozy M5", "Momcozy M9", "Momcozy S12 Pro", "Momcozy V1", "Momcozy V2"],
    },
    {
        "brand": "Lansinoh",
        "product_line": "吸奶器",
        "dtc_domain": "lansinoh.com",
        "dtc_review_url": "https://lansinoh.com/collections/breast-pumps",
        "dtc_regions": ["US", "GB", "CA"],
        "google_review_query": 'site:lansinoh.com "review" ("suction" OR "pain" OR "leak")',
        "amazon_brand_filter": "Lansinoh",
        "key_models": ["Lansinoh Smartpump 2.0", "Lansinoh Manual Breast Pump"],
    },
    {
        "brand": "Motif Medical",
        "product_line": "吸奶器",
        "dtc_domain": "motifmedical.com",
        "dtc_review_url": "https://www.motifmedical.com/collections/breast-pumps",
        "dtc_regions": ["US"],
        "google_review_query": 'site:motifmedical.com "review" ("suction" OR "issue" OR "returned")',
        "amazon_brand_filter": "Motif Medical",
        "key_models": ["Motif Aura", "Motif Duo", "Motif Luna"],
    },
    {
        "brand": "Haakaa",
        "product_line": "吸奶器",
        "dtc_domain": "haakaa.com",
        "dtc_review_url": "https://www.haakaa.com/collections/breast-pumps",
        "dtc_regions": ["US", "AU", "GB", "CA"],
        "google_review_query": 'site:haakaa.com "review" ("suction" OR "spill" OR "silicone")',
        "amazon_brand_filter": "Haakaa",
        "key_models": ["Haakaa Silicone Breast Pump", "Haakaa Wearable Pump"],
    },

    # ── 喂养电器 ──
    {
        "brand": "Philips Avent",
        "product_line": "喂养电器",
        "dtc_domain": "philips.com",
        "dtc_review_url": "https://www.philips.com/c-m-mo/philips-avent-bottle-warmers-sterilizers",
        "dtc_regions": ["US", "GB", "DE", "FR", "ES", "AU", "CA"],
        "google_review_query": 'site:philips.com "avent" "review" ("slow" OR "uneven" OR "difficult")',
        "amazon_brand_filter": "Philips Avent",
        "key_models": ["Avent Fast Bottle Warmer", "Avent 3-in-1 Sterilizer", "Avent Premium Sterilizer"],
        "local_domains": {
            "DE": "philips.de", "FR": "philips.fr", "ES": "philips.es",
            "GB": "philips.co.uk", "AU": "philips.com.au",
        },
    },
    {
        "brand": "Tommee Tippee",
        "product_line": "喂养电器",
        "dtc_domain": "tommeetippee.com",
        "dtc_review_url": "https://www.tommeetippee.com/en-us/feeding",
        "dtc_regions": ["US", "GB", "AU"],
        "google_review_query": 'site:tommeetippee.com "review" ("leak" OR "slow" OR "not compatible")',
        "amazon_brand_filter": "Tommee Tippee",
        "key_models": ["Closer to Nature Sterilizer", "Perfect Prep Machine", "Easi-warm Bottle Warmer"],
    },
    {
        "brand": "Dr. Brown's",
        "product_line": "喂养电器",
        "dtc_domain": "drbrownsbaby.com",
        "dtc_review_url": "https://www.drbrownsbaby.com/product-type/feeding/",
        "dtc_regions": ["US", "GB", "CA"],
        "google_review_query": 'site:drbrownsbaby.com "review" ("colic" OR "hard to clean" OR "parts")',
        "amazon_brand_filter": "Dr. Brown",
        "key_models": ["Dr. Brown's Deluxe Bottle Sterilizer", "Dr. Brown's Bottle Warmer"],
    },
    {
        "brand": "Baby Brezza",
        "product_line": "喂养电器",
        "dtc_domain": "babybrezza.com",
        "dtc_review_url": "https://www.babybrezza.com/collections/all",
        "dtc_regions": ["US", "CA"],
        "google_review_query": 'site:babybrezza.com "review" ("formula" OR "dispenser" OR "error" OR "not accurate")',
        "amazon_brand_filter": "Baby Brezza",
        "key_models": ["Formula Pro Advanced", "Baby Brezza Sterilizer Dryer", "One Step Sterilizer"],
    },
    {
        "brand": "Chicco",
        "product_line": "喂养电器",
        "dtc_domain": "chiccousa.com",
        "dtc_review_url": "https://www.chiccousa.com/shop-all-feeding/",
        "dtc_regions": ["US", "ES", "MX"],
        "google_review_query": 'site:chiccousa.com "review" ("warm" OR "sterilize" OR "problem")',
        "amazon_brand_filter": "Chicco",
        "key_models": ["Chicco NaturalFit Sterilizer", "Chicco Bottle Warmer"],
        "local_domains": {"ES": "chicco.es", "MX": "chicco.com.mx"},
    },
    {
        "brand": "NUK",
        "product_line": "喂养电器",
        "dtc_domain": "nuk.com",
        "dtc_review_url": "https://www.nuk.com/products/feeding",
        "dtc_regions": ["US", "DE", "GB"],
        "google_review_query": 'site:nuk.com "review" ("warming" OR "parts" OR "difficult")',
        "amazon_brand_filter": "NUK",
        "key_models": ["NUK Thermo Express Bottle Warmer", "NUK Vario Express Sterilizer"],
        "local_domains": {"DE": "nuk.de"},
    },

    # ── 家居出行 ──
    {
        "brand": "Bugaboo",
        "product_line": "家居出行",
        "dtc_domain": "bugaboo.com",
        "dtc_review_url": "https://www.bugaboo.com/strollers/",
        "dtc_regions": ["US", "GB", "DE", "FR", "ES", "AU", "CA"],
        "google_review_query": 'site:bugaboo.com "review" ("heavy" OR "price" OR "fold" OR "wheel")',
        "amazon_brand_filter": "Bugaboo",
        "key_models": ["Bugaboo Fox 5", "Bugaboo Dragonfly", "Bugaboo Butterfly"],
    },
    {
        "brand": "UPPAbaby",
        "product_line": "家居出行",
        "dtc_domain": "uppababy.com",
        "dtc_review_url": "https://uppababy.com/strollers/",
        "dtc_regions": ["US", "CA", "GB", "AU"],
        "google_review_query": 'site:uppababy.com "review" ("heavy" OR "bulky" OR "fold" OR "price")',
        "amazon_brand_filter": "UPPAbaby",
        "key_models": ["UPPAbaby Vista V3", "UPPAbaby Cruz V3", "UPPAbaby Minu V2"],
    },
    {
        "brand": "Cybex",
        "product_line": "家居出行",
        "dtc_domain": "cybex-online.com",
        "dtc_review_url": "https://cybex-online.com/strollers",
        "dtc_regions": ["US", "GB", "DE", "FR"],
        "google_review_query": 'site:cybex-online.com "review" ("heavy" OR "fold" OR "canopy" OR "recline")',
        "amazon_brand_filter": "CYBEX",
        "key_models": ["Cybex Priam", "Cybex Mios", "Cybex Libelle", "Cybex Eezy S Twist"],
    },
    {
        "brand": "Babyzen",
        "product_line": "家居出行",
        "dtc_domain": "babyzen.com",
        "dtc_review_url": "https://www.babyzen.com/en/strollers",
        "dtc_regions": ["US", "GB", "FR", "DE"],
        "google_review_query": 'site:babyzen.com "review" ("recline" OR "canopy" OR "expensive" OR "newborn")',
        "amazon_brand_filter": "BABYZEN",
        "key_models": ["YOYO2", "YOYO Bassinet"],
    },
    {
        "brand": "Graco",
        "product_line": "家居出行",
        "dtc_domain": "gracobaby.com",
        "dtc_review_url": "https://www.gracobaby.com/strollers/",
        "dtc_regions": ["US", "CA", "GB"],
        "google_review_query": 'site:gracobaby.com "review" ("heavy" OR "fold" OR "wheel" OR "recline")',
        "amazon_brand_filter": "Graco",
        "key_models": ["Graco Modes Pramette", "Graco Jetsetter", "Graco FastAction"],
    },
]


def get_brands_by_line(product_line: str) -> list[dict]:
    return [b for b in COMPETITOR_BRANDS if b["product_line"] == product_line]


def get_brands_by_region(country_code: str) -> list[dict]:
    return [b for b in COMPETITOR_BRANDS if country_code in b["dtc_regions"]]


def get_brands_by_line_and_region(product_line: str, country_code: str) -> list[dict]:
    return [
        b for b in COMPETITOR_BRANDS
        if b["product_line"] == product_line and country_code in b["dtc_regions"]
    ]


def get_dtc_domain_for_country(brand: dict, country_code: str) -> str:
    local = brand.get("local_domains", {})
    return local.get(country_code, brand["dtc_domain"])


ALL_PRODUCT_LINES = ["吸奶器", "喂养电器", "家居出行", "内衣服饰", "智能母婴电器"]

AMAZON_DOMAINS = {
    "US": "amazon.com", "CA": "amazon.ca", "GB": "amazon.co.uk",
    "DE": "amazon.de", "FR": "amazon.fr", "ES": "amazon.es",
    "MX": "amazon.com.mx", "AE": "amazon.ae", "AU": "amazon.com.au",
    "SA": "amazon.sa",
}

TOP10_COUNTRIES = [
    {"country": "美国", "code": "US"}, {"country": "加拿大", "code": "CA"},
    {"country": "英国", "code": "GB"}, {"country": "德国", "code": "DE"},
    {"country": "法国", "code": "FR"}, {"country": "西班牙", "code": "ES"},
    {"country": "墨西哥", "code": "MX"}, {"country": "阿联酋", "code": "AE"},
    {"country": "澳大利亚", "code": "AU"}, {"country": "沙特阿拉伯", "code": "SA"},
]

TOP11_20_COUNTRIES = [
    {"country": "中国", "code": "CN"}, {"country": "意大利", "code": "IT"},
    {"country": "马来西亚", "code": "MY"}, {"country": "奥地利", "code": "AT"},
    {"country": "越南", "code": "VN"}, {"country": "波兰", "code": "PL"},
    {"country": "菲律宾", "code": "PH"}, {"country": "泰国", "code": "TH"},
    {"country": "荷兰", "code": "NL"}, {"country": "比利时", "code": "BE"},
]

TOP20_COUNTRIES = TOP10_COUNTRIES + TOP11_20_COUNTRIES
