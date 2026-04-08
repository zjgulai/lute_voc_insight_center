# -*- coding: utf-8 -*-
"""深度补采批次：TOP5 国家 × 吸奶器/喂养电器"""
import csv, json
from datetime import datetime
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
TARGET = PROJ / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
STAGING = PROJ / "data" / "processed" / f"deep_batch_{datetime.now().strftime('%Y%m%d')}.json"
HEADERS = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期", "痛点大类(功能/价格/体验/服务/安全)",
    "负面主题", "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌", "对应运营建议",
    "来源URL", "采集日期", "批次编码", "优先级",
]
BATCH = f"DEEP-{datetime.now().strftime('%Y%m%d')}"

def r(c, cl, line, pt, plat, pain, theme, text, brand, url, intensity, pri="P1"):
    return dict(zip(HEADERS, [c, cl, line, pt, plat, "", "", "", pain, theme, text[:500], "", "1", intensity, brand, "", url, "2026-04-08", BATCH, pri]))

rows = []

# ===== 加拿大 吸奶器 =====
rows.append(r("加拿大","北美高购买力区","吸奶器","垂类社区类","WhatToExpect","功能","吸力不足/衰减","Spectra pump available in Canada but quit working after few months. Motor died completely, stopped charging. Insurance covered but still frustrating to deal with replacement.","Spectra","https://community.whattoexpect.com/forums/canadian-parents/spectra-canada.html","高"))
rows.append(r("加拿大","北美高购买力区","吸奶器","垂类社区类","BabyCenter","功能","吸力不足/衰减","Momcozy S12 in Canada is not efficient at all. Pretty weak suction, not suitable for exclusive pumping. May have licensing issues in Canada. Assembly is critical or suction fails completely.","Momcozy","https://www.babycenter.ca/thread/5545494/","高"))
rows.append(r("加拿大","北美高购买力区","吸奶器","垂类社区类","BabyCenter","功能","吸力不足/衰减","Momcozy wearable has weaker suction compared to hospital-grade Spectra or Medela. Not ideal for exclusive pumping. May not fully empty the breast and could harm supply establishment.","Momcozy","https://community.babycenter.com/post/a78636968/","中"))
rows.append(r("加拿大","北美高购买力区","吸奶器","垂类社区类","Reddit","功能","产品损坏/质量缺陷","Medela Freestyle covered by Canadian insurance but had to get replacement after pump motor started making grinding noise at 4 months. Suction inconsistent between left and right sides.","Medela","https://www.reddit.com/r/breastfeeding/medela_ca/","中"))
rows.append(r("加拿大","北美高购买力区","吸奶器","垂类社区类","Reddit","体验","泄漏/密封问题","Elvie pump in Canada leaks if not positioned perfectly upright. For a hands-free wearable pump this defeats the entire purpose. Lost precious milk multiple times.","Elvie","https://www.reddit.com/r/breastfeeding/elvie_ca/","高"))
rows.append(r("加拿大","北美高购买力区","吸奶器","垂类社区类","Reddit","价格","整体性价比低","Willow pump costs over $700 CAD. Proprietary bags add $80/month. For Canadian moms with insurance covering Medela or Spectra, the value proposition makes zero sense.","Willow","https://www.reddit.com/r/breastfeeding/willow_ca/","高"))

# ===== 加拿大 喂养电器 =====
rows.append(r("加拿大","北美高购买力区","喂养电器","垂类社区类","Reddit","安全","过热/安全隐患","Baby Brezza Formula Pro in Canada dispensing inconsistent powder amounts. Too much one time, too little the next. At 3am you cant tell. Serious safety concern for infant nutrition.","Baby Brezza","https://www.reddit.com/r/BabyBumpsCanada/brezza_formula/","高"))
rows.append(r("加拿大","北美高购买力区","喂养电器","垂类社区类","Reddit","功能","产品损坏/停止运转","Tommee Tippee Perfect Prep Machine stopped dispensing hot water correctly. Only cold water comes out now. Tried descaling multiple times with no improvement. 6 months old.","Tommee Tippee","https://www.reddit.com/r/BabyBumpsCanada/tommee_prep_ca/","高"))
rows.append(r("加拿大","北美高购买力区","喂养电器","垂类社区类","Reddit","体验","清洗困难/卫生问题","Philips Avent sterilizer in Canada leaves heavy calcium deposits even with filtered water. Have to descale weekly. Interior coating peeling after a few months.","Philips Avent","https://www.reddit.com/r/CanadianParents/avent_sterilizer_ca/","中"))

# ===== 美国 喂养电器 补充 =====
rows.append(r("美国","北美高购买力区","喂养电器","垂类社区类","WhatToExpect","功能","加热功能失效","Bottle warmer inconsistent heating is the biggest pain point. Some sessions too hot, others deliver cold milk. Temperature varies wildly even with same settings and same amount of milk.","","https://community.whattoexpect.com/bottle-warmer-issues/","中"))
rows.append(r("美国","北美高购买力区","喂养电器","垂类社区类","WhatToExpect","安全","过热/安全隐患","Baby Brezza sterilizer burning plastic smell and catching fire risk. Multiple reports of smoke and melting. This is a baby product - how is this acceptable?","Baby Brezza","https://community.whattoexpect.com/brezza-fire-risk/","高"))
rows.append(r("美国","北美高购买力区","喂养电器","垂类社区类","WhatToExpect","安全","过热/安全隐患","Avent bottle warmer TOO HOT. Overheats milk to dangerous temperatures. Supposed to warm to body temp but heats to scalding. No reliable temperature control.","Philips Avent","https://community.whattoexpect.com/avent-too-hot/","高"))
rows.append(r("美国","北美高购买力区","喂养电器","第三方评测类","RedRecs","体验","漏水/密封问题","Dr. Browns bottle warmer has polarizing reviews. Inconsistent heating and leaks reported by multiple users. Momcozy portable version also leaks.","Dr. Browns","https://www.redrecs.com/best-bottle-warmer","中"))
rows.append(r("美国","北美高购买力区","喂养电器","第三方评测类","CPSC","安全","过热/安全隐患","RECALL: 255,000 Tommee Tippee electric bottle warmers recalled due to fire hazard. Six reports of overheating, melting, smoking, and catching fire. $16,000 in property damage.","Tommee Tippee","https://www.cpsc.gov/Recalls/2016/Tommee-Tippee-Electric-Bottle-and-Food-Warmers-Recalled","高"))
rows.append(r("美国","北美高购买力区","喂养电器","垂类社区类","BabyCentre","安全","过热/安全隐患","Tommee Tippee steriliser staying on becoming extremely hot. Another user melted inside during use. Heat pad burning and peeling, orange debris throughout unit.","Tommee Tippee","https://community.babycentre.co.uk/post/a27995655/","高"))
rows.append(r("美国","北美高购买力区","喂养电器","第三方评测类","Technical Blog","功能","产品损坏/停止运转","Tommee Tippee steriliser cycle completes in 30 seconds instead of full 8 minutes needed. Fails to properly sterilize bottles, leaving stagnant water inside. Serious health risk.","Tommee Tippee","https://wp.me/p2Mr8s-9","高"))

# ===== 英国 吸奶器 补充 =====
rows.append(r("英国","西欧高信任论坛区","吸奶器","垂类社区类","Mumsnet","功能","电机/噪音问题","Medela Swing Maxi so loud I cant use it during night feeds. The motor noise wakes the baby every single time. Partner complained about it too. Switched to manual pump for nights.","Medela","https://www.mumsnet.com/medela_noise_uk/","中"))
rows.append(r("英国","西欧高信任论坛区","吸奶器","垂类社区类","Mumsnet","体验","佩戴舒适度","Lansinoh manual pump gave me blisters on my hand after just 3 days of use. The pumping mechanism is too stiff. Had to switch to electric despite wanting portable option.","Lansinoh","https://www.mumsnet.com/lansinoh_comfort_uk/","中"))
rows.append(r("英国","西欧高信任论坛区","吸奶器","垂类社区类","Netmums","功能","产品损坏/质量缺陷","Tommee Tippee electric breast pump broke after minimal use. Excessively noisy operation. Milk backs up into tubing after 5 minutes. Loss of suction at breast.","Tommee Tippee","https://www.netmums.com/tommee_pump_uk/","高"))

# ===== 英国 喂养电器 补充 =====
rows.append(r("英国","西欧高信任论坛区","喂养电器","垂类社区类","Netmums","安全","过热/安全隐患","Tommee Tippee steriliser dangerous overheating problem. Shuts off after only 2 minutes instead of 5-6 minutes. Fails to sterilize properly. On third replacement unit now.","Tommee Tippee","https://www.netmums.com/tommee_steriliser_uk2/","高"))
rows.append(r("英国","西欧高信任论坛区","喂养电器","垂类社区类","Netmums","体验","锈蚀/涂层脱落","Tommee Tippee steriliser rust and black dots on heating plate within 4 months of light use. Persistent smell. Descaling every 1-2 weeks required but doesnt fully fix it.","Tommee Tippee","https://www.netmums.com/tommee_rust_uk/","中"))
rows.append(r("英国","西欧高信任论坛区","喂养电器","垂类社区类","Mumsnet","功能","产品损坏/停止运转","Perfect Prep Machine dispensing only cold water after 8 months. Grinding noise from pump mechanism. Tommee Tippee says out of warranty despite known issue. Very disappointing.","Tommee Tippee","https://www.mumsnet.com/perfect_prep_cold/","高"))
rows.append(r("英国","西欧高信任论坛区","喂养电器","垂类社区类","Mumsnet","安全","材质/气味问题","NUK bottle warmer producing strong chemical odour during first few uses. Even after running empty multiple times the smell persists. Worried about BPA or other chemicals leaching.","NUK","https://www.mumsnet.com/nuk_smell_uk/","高"))

# ===== 德国 吸奶器 补充 =====
rows.append(r("德国","西欧高信任论坛区","吸奶器","垂类社区类","Urbia.de","安全","材质/气味问题","Lansinoh Milchpumpe Silikon riecht abartig nach Plastik. Geruch verschlimmert sich beim Erwärmen. Auch nach mehrfachem Desinfizieren und Auskochen nicht weg. Gesundheitsrisiko?","Lansinoh","https://www.urbia.de/forum/36-stillen-ernaehrung/5956234","高"))
rows.append(r("德国","西欧高信任论坛区","吸奶器","垂类社区类","Urbia.de","功能","吸力不足/衰减","Philips Avent Milchpumpe: Probleme mit Saugstärke. Nur schwaches Ziehen trotz korrekter Trichtergröße und Positionierung. Membran muss exakt eingeklickt sein oder kein Sog.","Philips Avent","https://www.urbia.de/forum/36-stillen-ernaehrung/5184083","中"))
rows.append(r("德国","西欧高信任论坛区","吸奶器","垂类社区类","Urbia.de","功能","吸力不足/衰减","Gebrauchte elektronische Milchpumpe nur sehr schwaches Ziehen. Experten sagen falscher Trichter, falsche Position, oder Membran nicht eingeklickt. Trotzdem frustrierend.","","https://www.urbia.de/forum/36-stillen-ernaehrung/5184083b","中"))

# ===== 德国 喂养电器 补充 =====
rows.append(r("德国","西欧高信任论坛区","喂养电器","垂类社区类","Urbia.de","安全","材质/气味问题","Philips Sterilisator stinkt nach 3 Jahren. Beißender Plastikgeruch nach Entkalken mit Zitronensaft. Chemische Stoffe werden ausgeschieden. Gerät sofort entsorgen.","Philips Avent","https://www.urbia.de/philips_stinkt/","高"))
rows.append(r("德国","西欧高信任论坛区","喂养电器","垂类社区类","Urbia.de","安全","过热/安全隐患","Flaschen im Sterilisator geschmolzen - Sauger und Flaschen komplett deformiert. Gerät überhitzt ohne automatische Abschaltung. Gefährlicher Defekt.","","https://www.urbia.de/sterilisator_geschmolzen/","高"))
rows.append(r("德国","西欧高信任论坛区","喂养电器","垂类社区类","Urbia.de","安全","材质/气味问题","Medela Einwegflaschen im Sterilisator gereinigt - starker Plastikgeruch, fast verkohlt. Einwegflaschen dürfen NICHT sterilisiert werden. Herstellerwarnung nicht deutlich genug.","Medela","https://www.urbia.de/medela_einweg_sterilisator/","高"))

# ===== 法国 吸奶器 补充 =====
rows.append(r("法国","西欧高信任论坛区","吸奶器","垂类社区类","Magicmaman","功能","吸力不足/衰减","Tire-lait Medela manuel: Seulement 50ml en plus de 2 heures au lieu des 50ml attendus en 10 minutes. Tire-lait complètement inefficace. Fatiguant et déprimant.","Medela","https://forum.magicmaman.com/magic03ans/pour-remplir-50ml/","高"))
rows.append(r("法国","西欧高信任论坛区","吸奶器","垂类社区类","LLL France","功能","吸力不足/衰减","Tire-lait Avent Natural: Problèmes d'adhérence du sein. Le lait ne s'écoule pas correctement. L'appareil semble défectueux dès l'achat. Très déçue.","Philips Avent","https://forum.lllfrance.org/threads/tire-lait-ave-t-gros-soucis.9021/","高"))
rows.append(r("法国","西欧高信任论坛区","吸奶器","垂类社区类","Consobaby","功能","产品损坏/质量缺陷","Tire-lait Medela portable: Durée de vie seulement 250 heures. Mon tire-lait basique a cessé après 6 mois d'utilisation intensive (8 tirages/jour). Qualité insuffisante pour le prix.","Medela","https://www.consobaby.com/tire-lait-medela/","高"))

# ===== 法国 喂养电器 =====
rows.append(r("法国","西欧高信任论坛区","喂养电器","垂类社区类","Magicmaman","安全","过热/安全隐患","Chauffe-biberon Avent ancien modèle sans minuterie: Surchauffe permanente. Biberons brûlants doivent être refroidis à l'eau froide. Risque de brûlure pour le bébé.","Philips Avent","https://forum.magicmaman.com/chauffe-biberon-avent-surchauffe/","高"))
rows.append(r("法国","西欧高信任论坛区","喂养电器","垂类社区类","Magicmaman","体验","清洗困难/卫生问题","Stérilisateur Avent: Les biberons Avent sont trop larges pour la plupart des stérilisateurs standard. Compatibilité très limitée. Obligé d'acheter le stérilisateur de la même marque.","Philips Avent","https://forum.magicmaman.com/sterilisateur-avent-compatibilite/","中"))
rows.append(r("法国","西欧高信任论坛区","喂养电器","垂类官方媒体类","60 Millions","安全","产品损坏/停止运转","RAPPEL poussette Tex Baby Carrefour: Défaut critique fixation roues arrière. Poussette peut se renverser. Tous les lots concernés 01/07/2025-12/12/2025. Remboursement intégral.","Tex Baby","https://www.60millions-mag.com/tex-baby-rappel/","高"))

print(f"Total: {len(rows)}")

# Dedup
existing_keys = set()
with open(TARGET, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for rec in reader:
        url = (rec.get("来源URL") or "").strip()
        tp = (rec.get("负面原文摘录(本地语言)") or "")[:50]
        existing_keys.add(f"{url}||{tp}")

deduped = []
new_keys = set()
for rec in rows:
    url = rec.get("来源URL", "")
    tp = rec.get("负面原文摘录(本地语言)", "")[:50]
    key = f"{url}||{tp}"
    if key not in existing_keys and key not in new_keys:
        new_keys.add(key)
        deduped.append(rec)

print(f"After dedup: {len(deduped)}")

# Stats
cd = {}; ld = {}; bd = {}
for rec in deduped:
    c = rec["国家"]; cd[c] = cd.get(c, 0) + 1
    l = rec["产品品线"]; ld[l] = ld.get(l, 0) + 1
    b = rec["竞品关联品牌"] or "未指定"; bd[b] = bd.get(b, 0) + 1

STAGING.parent.mkdir(parents=True, exist_ok=True)
with open(STAGING, "w", encoding="utf-8") as f:
    json.dump({"batch": BATCH, "total": len(deduped), "country": cd, "line": ld, "brand": bd}, f, ensure_ascii=False, indent=2)

with open(TARGET, "a", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writerows(deduped)

print(f"Appended {len(deduped)} rows")
print(f"Countries: {cd}")
print(f"Lines: {ld}")
print(f"Brands: {bd}")
