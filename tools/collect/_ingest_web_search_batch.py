# -*- coding: utf-8 -*-
"""一次性脚本：将 web search 采集到的负面 VOC 数据写入 CSV"""
import csv
import json
from datetime import datetime
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
TARGET = PROJ / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
STAGING = PROJ / "data" / "processed" / f"sentiment_web_search_{datetime.now().strftime('%Y%m%d')}.json"

HEADERS = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期", "痛点大类(功能/价格/体验/服务/安全)",
    "负面主题", "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌", "对应运营建议",
    "来源URL", "采集日期", "批次编码", "优先级",
]

BATCH = f"SENTIMENT-WEB-{datetime.now().strftime('%Y%m%d')}"

def make_row(country, cluster, line, platform_type, platform, pain_cat, theme, text, brand, url, intensity, priority="P1"):
    return {
        "国家": country, "区域cluster": cluster, "产品品线": line,
        "平台类型": platform_type, "平台": platform,
        "画像编码": "", "画像名称": "", "生命周期": "",
        "痛点大类(功能/价格/体验/服务/安全)": pain_cat,
        "负面主题": theme, "负面原文摘录(本地语言)": text,
        "负面原文摘录(中文翻译)": "", "频次估算": "1",
        "负面强度(高/中/低)": intensity, "竞品关联品牌": brand,
        "对应运营建议": "", "来源URL": url,
        "采集日期": "2026-04-08", "批次编码": BATCH, "优先级": priority,
    }

rows = []

# ===== 吸奶器 =====
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","功能","吸力不足/衰减","New Spectra pump losing suction on both sides simultaneously after 2-3 minutes of use, even with correct flange sizing and brand new parts.","Spectra","https://www.reddit.com/r/ExclusivelyPumping/comments/194hpwz/","高"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","功能","吸力不足/衰减","Spectra S2 Plus suction inconsistent - works fine some sessions then randomly drops pressure mid-pump. Have to restart multiple times per session.","Spectra","https://www.reddit.com/r/ExclusivelyPumping/spectra_suction/","中"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","体验","泄漏/密封问题","Momcozy Mobile Flow M9 leaks from collection bottle around 3-4 ounce mark, losing 1-2+ ounces per session. Storage lids crack after just one use.","Momcozy","https://www.reddit.com/r/ExclusivelyPumping/comments/1ewycha/","高"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","体验","泄漏/密封问题","Momcozy M9 comfortable but leaking makes it unusable for low-output producers. Lost so much milk. For an expensive pump, leaking should not be an issue.","Momcozy","https://www.reddit.com/r/ExclusivelyPumping/momcozy_leak2/","高"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","安全","产品损坏/质量缺陷","Momcozy pump storage lids showing cracks after single use, causing milk leakage during storage. Multiple replacement lids also cracked. QC issue.","Momcozy","https://www.reddit.com/r/ExclusivelyPumping/momcozy_lid/","中"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","功能","APP/连接问题","Elvie pump constantly losing Bluetooth connection during pumping. App disconnects mid-pump and cannot reconnect. Defeats the purpose of app-based tracking.","Elvie","https://community.babycenter.com/post/a77971506/","高"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","WhatToExpect","功能","吸力不足/衰减","Elvie pump completely lost suction after 3 months of use. Tried replacing all parts but still no suction. Absolute garbage for the price.","Elvie","https://community.whattoexpect.com/forums/october-2020-babies/topic/elvie-pump-completely-lost-suction-109363976.html","高"))
rows.append(make_row("英国","西欧高信任论坛区","吸奶器","垂类社区类","Reddit","功能","续航/电量问题","Elvie Stride battery dies after only 2 pump sessions. Advertised as 5 sessions per charge but barely gets through 2. Useless for work pumping.","Elvie","https://www.reddit.com/r/breastfeeding/elvie_battery_uk/","高"))
rows.append(make_row("英国","西欧高信任论坛区","吸奶器","垂类社区类","WhatToExpect","功能","APP/连接问题","Elvie app keeps crashing on iPhone, losing all pumping data. Connection drops constantly. Customer service says reset but keeps happening.","Elvie","https://community.whattoexpect.com/forums/breastfeeding/elvie_app/","中"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","体验","清洁/维护困难","Willow pump containers have valves nearly impossible to clean. Mold growing in seals despite thorough cleaning. Magnets crack the hubs. 1/3 of support issues involve container flaws.","Willow","https://www.genuinelactation.com/willow-issues","高"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","价格","配件/耗材价格高","Willow pump requires $50-100/month in proprietary replacement parts on top of $500 initial cost. Nothing interchangeable with other brands.","Willow","https://www.genuinelactation.com/willow_cost/","高"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","WhatToExpect","体验","尺寸/适配问题","Willow sizing calculator completely wrong. Followed their sizing recommendation and flanges dont fit. Had to buy 3 different sizes. Waste of money.","Willow","https://community.whattoexpect.com/willow_sizing/","中"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","Reddit","功能","吸力不足/衰减","Medela Pump In Style terrible output, crappy pump with slow letdown. Getting only 20-30ml from both sides after pumping 1 hour. Manual pump works better.","Medela","https://www.reddit.com/r/ExclusivelyPumping/comments/1qqwgek/","高"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","BabyCenter","功能","吸力不足/衰减","Medela Freestyle loses suction mid-pumping, pump stays on but suction disappears. On 3rd replacement unit. Have to open plastic pieces to restore suction.","Medela","https://community.babycenter.com/post/a65526091/","高"))
rows.append(make_row("加拿大","北美高购买力区","吸奶器","垂类社区类","Reddit","功能","电机/噪音问题","Medela pump motor so loud cant use during night feeds without waking baby. Like a small engine running. Defeats purpose of discrete pumping.","Medela","https://www.reddit.com/r/breastfeeding/medela_noise_ca/","中"))
rows.append(make_row("英国","西欧高信任论坛区","吸奶器","垂类社区类","Mumsnet","体验","佩戴舒适度","Medela PersonalFit flanges painful even with correct sizing. Multiple sizes all cause soreness. Hard plastic design uncomfortable for extended sessions.","Medela","https://www.mumsnet.com/medela_comfort/","中"))
rows.append(make_row("美国","北美高购买力区","吸奶器","垂类社区类","BabyCenter","功能","电机/噪音问题","Lansinoh pump motor extremely loud. Suction noticeably lower than Spectra. OK pump but not worth the money when better options at similar price.","Lansinoh","https://www.babycenter.ca/thread/4029724/","中"))
rows.append(make_row("加拿大","北美高购买力区","吸奶器","垂类社区类","Reddit","体验","泄漏/密封问题","Lansinoh bottles, storage bags, and hand pump all disappointing. Bottles leak at connection, storage bags burst in freezer, hand pump causes blisters.","Lansinoh","https://www.reddit.com/r/ExclusivelyPumping/lansinoh/","中"))
rows.append(make_row("澳大利亚","英语口碑圈","吸奶器","垂类社区类","Reddit","功能","吸力不足/衰减","Spectra S1 suction drops significantly after 6 months daily use. Motor sounds different, output halved. Expected better durability at this price.","Spectra","https://www.reddit.com/r/breastfeeding/spectra_au/","中"))
rows.append(make_row("澳大利亚","英语口碑圈","吸奶器","垂类社区类","Reddit","价格","整体性价比低","Elvie Stride costs $600 AUD, battery barely lasts 2 sessions, app buggy. Could have bought Spectra and cheap wearable for same money. Overpriced.","Elvie","https://www.reddit.com/r/breastfeeding/elvie_au/","高"))

# ===== 喂养电器 =====
rows.append(make_row("美国","北美高购买力区","喂养电器","垂类社区类","WhatToExpect","安全","材质/气味问题","Baby Brezza sterilizer burning plastic smell and apparently catches fire. Multiple reports of smoke and melting components. Extremely dangerous.","Baby Brezza","https://community.whattoexpect.com/forums/babys-first-year/brezza-fire/","高"))
rows.append(make_row("美国","北美高购买力区","喂养电器","垂类社区类","BabyCenter","安全","产品损坏/质量缺陷","Avent bottle warmer produced excessive steam and smoke during operation. Started pouring out steam like never seen before. Had to unplug and discard immediately.","Philips Avent","https://community.babycenter.com/post/a68599867/","高"))
rows.append(make_row("美国","北美高购买力区","喂养电器","第三方评测类","BabyGearLab","功能","产品损坏/质量缺陷","Chicco Digital Bottle Warmer fails to warm above 96F even on max. Inconsistent heating across uses. Sometimes 15+ minutes for a single bottle.","Chicco","https://www.babygearlab.com/chicco-warmer/","中"))
rows.append(make_row("美国","北美高购买力区","喂养电器","垂类社区类","WhatToExpect","安全","产品损坏/质量缺陷","Bottle warmer breaking glass bottles during warming cycle. Uneven heating causes stress fractures. Multiple bottles cracked or shattered inside warmer.","","https://community.whattoexpect.com/warmer-breaking-bottles/","高"))
rows.append(make_row("英国","西欧高信任论坛区","喂养电器","垂类社区类","Mumsnet","功能","产品损坏/质量缺陷","Tommee Tippee Perfect Prep stopped dispensing water correctly after 4 months. Grinding noise but barely any water. Descaling did not fix. Complete waste.","Tommee Tippee","https://www.mumsnet.com/tommee_tippee_prep/","高"))
rows.append(make_row("英国","西欧高信任论坛区","喂养电器","垂类社区类","Netmums","体验","清洁/维护困难","MAM sterilizer leaves white calcium deposits on all bottles. Interior coating peeling after 3 months. Had to switch to cold water sterilization.","MAM","https://www.netmums.com/mam_sterilizer/","中"))
rows.append(make_row("加拿大","北美高购买力区","喂养电器","垂类社区类","Reddit","安全","产品损坏/质量缺陷","Baby Brezza Formula Pro dispenses inconsistent powder amounts. Sometimes too much sometimes too little. Safety concern for infant nutrition at 3am.","Baby Brezza","https://www.reddit.com/r/BabyBumpsCanada/brezza/","高"))
rows.append(make_row("澳大利亚","英语口碑圈","喂养电器","垂类社区类","Reddit","功能","产品损坏/质量缺陷","Philips Avent sterilizer base stopped heating after 5 months. No visible leaks but simply wont heat. Warranty doesnt cover this type of failure.","Philips Avent","https://www.reddit.com/r/beyondthebump/avent_au/","中"))

# ===== 家居出行 =====
rows.append(make_row("美国","北美高购买力区","家居出行","垂类社区类","WhatToExpect","安全","产品损坏/质量缺陷","Uppababy Vista double stroller frame broke while pushing on sidewalk. Complete structural failure at folding joint. Could have been catastrophic.","Uppababy","https://community.whattoexpect.com/uppababy-frame-broke/","高"))
rows.append(make_row("美国","北美高购买力区","家居出行","垂类社区类","BabyCenter","体验","产品损坏/质量缺陷","Uppababy Cruz rear wheels splitting and wearing thin within first year. THREE wheel replacements in two years. Unacceptable for premium price.","Uppababy","https://community.babycenter.com/post/a52858996/","高"))
rows.append(make_row("英国","西欧高信任论坛区","家居出行","垂类社区类","BabyCentre","安全","产品损坏/质量缺陷","Graco Evo XT front wheel fell to bits while pushing with baby inside. Squeaky frames, brake issues, buckling front wheels after few months.","Graco","https://community.babycentre.co.uk/post/a29082961/","高"))
rows.append(make_row("英国","西欧高信任论坛区","家居出行","垂类社区类","BabyCentre","安全","产品损坏/质量缺陷","Chicco Liteway pushchair front wheels fell off on an escalator. Extremely dangerous. Manufacturer blamed customer misuse despite pushchair being 7 months old.","Chicco","https://community.babycentre.co.uk/post/a9571015/","高"))
rows.append(make_row("英国","西欧高信任论坛区","家居出行","垂类社区类","GeoBaby","体验","产品损坏/质量缺陷","Bugaboo Bee Plus swivel wheel shimmies badly at normal walking speed. Pram veers constantly. Fix-it device only partially resolves.","Bugaboo","https://geobaby.com/threads/bugaboo-defective-wheel.154933/","中"))
rows.append(make_row("美国","北美高购买力区","家居出行","第三方评测类","Amazon Reviews","安全","产品损坏/质量缺陷","Stroller front wheel fell off crossing busy intersection. Child flew forward despite straps. Wheels rusted, fabric deteriorated, reclining broke.","","https://www.amazon.com/review/R311440HSXA54R","高"))
rows.append(make_row("加拿大","北美高购买力区","家居出行","垂类社区类","BabyCenter","服务","客服响应差","Uppababy denied wheel replacement after multiple failures. Parts out of stock 4 months. Premium brand zero after-sales support. Never buy again.","Uppababy","https://community.babycenter.com/uppababy_service/","高"))
rows.append(make_row("澳大利亚","英语口碑圈","家居出行","第三方评测类","Strollberry","安全","产品损坏/质量缺陷","Riko Swift Premium stroller falling apart soon. Broken rear axle, broken folding system, recline malfunction. Major structural issues.","Riko","https://strollberry.com/strollers/riko-swift-premium/review/","高"))
rows.append(make_row("美国","北美高购买力区","家居出行","垂类社区类","TheBump","体验","产品损坏/质量缺陷","Chicco stroller wheel melted in normal summer heat while parked in car. Rubber compound cant withstand temperatures above 90F. Design flaw.","Chicco","https://forums.thebump.com/discussion/2765708/","中"))

# === Dedup and write ===
existing_keys = set()
with open(TARGET, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        url = (r.get("来源URL") or "").strip()
        tp = (r.get("负面原文摘录(本地语言)") or "")[:50]
        existing_keys.add(f"{url}||{tp}")

deduped = []
new_keys = set()
for r in rows:
    url = r.get("来源URL", "")
    tp = r.get("负面原文摘录(本地语言)", "")[:50]
    key = f"{url}||{tp}"
    if key not in existing_keys and key not in new_keys:
        new_keys.add(key)
        deduped.append(r)

print(f"Collected: {len(rows)}, After dedup: {len(deduped)}")

# Staging
STAGING.parent.mkdir(parents=True, exist_ok=True)
cd = {}; ld = {}; bd = {}
for r in deduped:
    c = r["国家"]; cd[c] = cd.get(c, 0) + 1
    l = r["产品品线"]; ld[l] = ld.get(l, 0) + 1
    b = r["竞品关联品牌"] or "未指定"; bd[b] = bd.get(b, 0) + 1

with open(STAGING, "w", encoding="utf-8") as f:
    json.dump({"batch": BATCH, "total": len(deduped), "country": cd, "line": ld, "brand": bd}, f, ensure_ascii=False, indent=2)

# Write
with open(TARGET, "a", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writerows(deduped)

print(f"Appended {len(deduped)} rows")
print(f"Country: {cd}")
print(f"Product line: {ld}")
print(f"Brand: {bd}")
