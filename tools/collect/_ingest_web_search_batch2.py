# -*- coding: utf-8 -*-
"""P1+P2 批次：Trustpilot/Netmums/德法西语区 VOC 数据写入"""
import csv, json
from datetime import datetime
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
TARGET = PROJ / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
STAGING = PROJ / "data" / "processed" / f"sentiment_web_p1p2_{datetime.now().strftime('%Y%m%d')}.json"
HEADERS = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期", "痛点大类(功能/价格/体验/服务/安全)",
    "负面主题", "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌", "对应运营建议",
    "来源URL", "采集日期", "批次编码", "优先级",
]
BATCH = f"SENTIMENT-P1P2-{datetime.now().strftime('%Y%m%d')}"

def r(country, cluster, line, ptype, platform, pain, theme, text, brand, url, intensity, priority="P1"):
    return dict(zip(HEADERS, [
        country, cluster, line, ptype, platform, "", "", "",
        pain, theme, text[:500], "", "1", intensity, brand, "", url, "2026-04-08", BATCH, priority,
    ]))

rows = []

# === Trustpilot Medela ===
rows.append(r("英国","西欧高信任论坛区","吸奶器","第三方评测类","Trustpilot","功能","吸力不足/衰减","Medela Swing double pump produces only dribbles of milk. Worse than a manual pump. Unable to return after opening. Total waste of money for expensive product.","Medela","https://uk.trustpilot.com/review/medela.co.uk","高"))
rows.append(r("美国","北美高购买力区","吸奶器","第三方评测类","Trustpilot","功能","产品损坏/质量缺陷","Medela pump no longer works as handsfree, must be plugged into mains. Not ideal for busy mum. Poor customer service for the price paid.","Medela","https://www.trustpilot.com/review/www.medela.com","高"))
rows.append(r("美国","北美高购买力区","吸奶器","第三方评测类","Trustpilot","价格","整体性价比低","Medela high-end pump is a total scam. Premium pricing is predatory toward desperate mothers. No genuine customer service, unanswered phones, slow email responses.","Medela","https://www.trustpilot.com/review/www.medela.com?page=2","高"))
rows.append(r("英国","西欧高信任论坛区","吸奶器","第三方评测类","Trustpilot","服务","客服响应差","Medela customer service non-existent. No genuine customer service department, phones not answered, emails take weeks. Impossible to process returns or warranty claims.","Medela","https://uk.trustpilot.com/review/medela.co.uk?service","中"))

# === Trustpilot Elvie ===
rows.append(r("英国","西欧高信任论坛区","吸奶器","第三方评测类","Trustpilot","功能","产品损坏/质量缺陷","Elvie pump malfunctioned shortly after purchase. Product stopped working within warranty but outside return window. No support options provided.","Elvie","https://uk.trustpilot.com/review/www.elvie.com","高"))
rows.append(r("英国","西欧高信任论坛区","吸奶器","第三方评测类","Trustpilot","体验","泄漏/密封问题","Elvie pump leaking issues reported by multiple users on Trustpilot. Suction problems and loss of suction power make it unreliable for exclusive pumping.","Elvie","https://uk.trustpilot.com/review/www.elvie.com?leak","高"))
rows.append(r("英国","西欧高信任论坛区","吸奶器","第三方评测类","Trustpilot","服务","客服响应差","Elvie customer service inconsistent. Some get quick replacements, others report unfulfilled replacement promises and long wait times. Unacceptable for premium pricing.","Elvie","https://uk.trustpilot.com/review/www.elvie.com?service","中"))

# === Trustpilot Willow ===
rows.append(r("美国","北美高购买力区","吸奶器","第三方评测类","Trustpilot","安全","产品损坏/质量缺陷","Willow pump rated Poor on Trustpilot (2.6/5). Container flaws, defective valves, seals that mold. Proprietary parts create ongoing expensive dependency.","Willow","https://uk.trustpilot.com/review/willowpump.com","高"))

# === Spectra 多国 ===
rows.append(r("美国","北美高购买力区","吸奶器","垂类社区类","BabyCenter","功能","产品损坏/质量缺陷","Spectra S1 is a POS - went through THREE pumps, each lasting only 5-7 months. Motors stop working, loss of suction, clicking sounds when turned on. Medela lasted much longer.","Spectra","https://community.babycenter.com/post/a77148455/","高"))
rows.append(r("美国","北美高购买力区","吸奶器","垂类社区类","WhatToExpect","功能","产品损坏/质量缺陷","Spectra pump quit working completely after few months. Stopped charging, motor dead. Customer service says flanges warp in sterilizers and refuses to replace.","Spectra","https://community.whattoexpect.com/spectra-quit/","高"))
rows.append(r("澳大利亚","英语口碑圈","吸奶器","第三方评测类","ProductReview","服务","客服响应差","Spectra customer service terrible. Flanges warp in sterilizers, company refuses replacement. Poor communication, delayed email responses, difficult warranty process.","Spectra","http://www.productreview.com.au/p/spectra-s1.html","中"))

# === Netmums Tommee Tippee ===
rows.append(r("英国","西欧高信任论坛区","喂养电器","垂类社区类","Netmums","安全","产品损坏/质量缺陷","Tommee Tippee steriliser shuts off after only 2 minutes instead of required 5-6 minutes. Fails to reach proper sterilization temperatures. Dangerous bacteria risk. On third machine.","Tommee Tippee","https://www.netmums.com/coffeehouse/1569534-dangerous-tommee-tippee.html","高"))
rows.append(r("英国","西欧高信任论坛区","喂养电器","垂类社区类","Netmums","体验","清洁/维护困难","Tommee Tippee steriliser rust and black dots on heating plate within 4 months. Persistent unpleasant smell. Requires descaling every 1-2 weeks. Complete deterioration.","Tommee Tippee","https://www.netmums.com/coffeehouse/1345694-issues-tommee-tippee.html","中"))
rows.append(r("英国","西欧高信任论坛区","吸奶器","垂类社区类","Netmums","功能","产品损坏/质量缺陷","Tommee Tippee electric breast pump broke after minimal use. Excessively noisy. Milk backs up into tubing after 5 minutes. Loss of suction despite suction in tubing.","Tommee Tippee","https://www.netmums.com/coffeehouse/381978-tommee-tippee-pump.html","高"))

# === 德语区 (德国) ===
rows.append(r("德国","西欧高信任论坛区","吸奶器","垂类社区类","Urbia.de","功能","吸力不足/衰减","Medela Milchpumpe: Keine Milch beim Abpumpen trotz voller Brust. Mit Philips Pumpe danach 120ml bekommen. Medela komplett unbrauchbar.","Medela","https://www.urbia.de/forum/36-stillen-ernaehrung/5889929","高"))
rows.append(r("德国","西欧高信任论坛区","吸奶器","垂类社区类","Urbia.de","功能","吸力不足/衰减","Elvie 2 Milchpumpe: Nur 90ml statt 150ml wie bei Medela Symphony. Verspäteter Milcheinschuss. Für 530 Euro Doppelpumpe absolut nicht akzeptabel.","Elvie","https://www.urbia.de/forum/36-stillen-ernaehrung/5562268","高"))
rows.append(r("德国","西欧高信任论坛区","吸奶器","垂类社区类","Urbia.de","安全","产品损坏/质量缺陷","Milchpumpe kaputt - Display geht nicht an, kein Strom trotz korrektem Anschluss. Geliehenes Gerät, Reparatur oder Ersatz unklar. Hilfe!","Medela","https://www.urbia.de/forum/9-baby/5748248","中"))
rows.append(r("德国","西欧高信任论坛区","家居出行","垂类社区类","Urbia.de","体验","产品损坏/质量缺陷","Kinderwagen Rad kaputt nach wenigen Monaten. Reifen geplatzt, Schlauch beschädigt. Reparatur beim Fahrradladen möglich aber ärgerlich für teuren Kinderwagen.","","https://www.urbia.de/forum/3-kleinkind/662959","中"))
rows.append(r("德国","西欧高信任论坛区","家居出行","垂类社区类","Urbia.de","安全","产品损坏/质量缺陷","Cybex Priam Kinderwagen mit defekter Bremse bei Gebrauchtkauf. Bremse funktioniert nicht zuverlässig. Sicherheitsrisiko für das Kind.","Cybex","https://www.urbia.de/forum/51-baby-vorbereitung/5883131","高"))
rows.append(r("德国","西欧高信任论坛区","家居出行","垂类社区类","Parents.at","体验","产品损坏/质量缺陷","Bugaboo Kinderwagen kaputt - Klemmung beim Zusammenklappen, Verschleißteile nach 2 Jahren. Reparatur außerhalb Garantie sehr teuer, da Teile zusammengeschweißt.","Bugaboo","https://www.parents.at/themen/bugaboo-kaputt.504442/","中"))
rows.append(r("德国","西欧高信任论坛区","家居出行","垂类社区类","Urbia.de","体验","产品损坏/质量缺陷","Joie Litetrax Buggy bekannte Qualitätsprobleme mit wackelnden Vorderrädern. Standardproblem laut Forum. Distanzgummis helfen nur teilweise.","Joie","https://www.urbia.de/forum/9-baby/5114295","中"))
rows.append(r("德国","西欧高信任论坛区","喂养电器","垂类社区类","Urbia.de","安全","材质/气味问题","Avent Sterilisator stinkt nach Plastik nach 3 Jahren Nutzung. Beißender Geruch nach dem Entkalken. Chemische Stoffe werden ausgeschieden. Sofort entsorgen.","Philips Avent","https://www.urbia.de/forum/36-stillen-ernaehrung/4501595","高"))
rows.append(r("德国","西欧高信任论坛区","喂养电器","垂类社区类","Urbia.de","安全","材质/气味问题","Medela Einweg-Babyflaschen im Sterilisator: Starker Plastikgeruch, fast verkohlt riechend. Einwegflaschen dürfen nicht sterilisiert werden - Sicherheitsrisiko.","Medela","https://www.urbia.de/forum/36-stillen-ernaehrung/5958370","高"))
rows.append(r("德国","西欧高信任论坛区","喂养电器","垂类社区类","Urbia.de","安全","产品损坏/质量缺陷","Flaschen im Sterilisator geschmolzen. Sauger und Flaschen komplett deformiert durch zu hohe Hitze. Gerät überhitzt ohne automatische Abschaltung.","","https://www.urbia.de/forum/9-baby/2872651","高"))

# === 法语区 (法国) ===
rows.append(r("法国","西欧高信任论坛区","吸奶器","垂类社区类","LLL France","功能","吸力不足/衰减","Tire-lait Avent Natural: Problèmes d'adhérence du sein et d'écoulement du lait. Appareil semble défectueux. Impossible de tirer correctement.","Philips Avent","https://forum.lllfrance.org/threads/tire-lait-ave-t-gros-soucis.9021/","高"))
rows.append(r("法国","西欧高信任论坛区","吸奶器","垂类社区类","LLL France","功能","产品损坏/质量缺陷","Tire-lait Medela portable: Durée de vie de seulement 250 heures. Un tire-lait basique a cessé de fonctionner après 6 mois d'utilisation intensive (8 tirages/jour).","Medela","https://forum.lllfrance.org/threads/avis-tire-lait.27659/","高"))
rows.append(r("法国","西欧高信任论坛区","家居出行","垂类官方媒体类","60 Millions","安全","产品损坏/质量缺陷","RAPPEL: Poussette convertible Tex Baby Carrefour - défaut critique fixation roues arrière. Risque de renversement et chute de l'enfant. Tous les lots concernés. Cesser utilisation immédiatement.","Tex Baby","https://www.60millions-mag.com/2025/12/15/carrefour-poussette-tex-baby-25269","高"))
rows.append(r("法国","西欧高信任论坛区","家居出行","垂类社区类","Forum Jumeaux","体验","产品损坏/质量缺陷","Problème de roue sur poussette Jané URGENT - roue avant cassée pendant promenade. Impossible de trouver pièce de rechange compatible. Poussette inutilisable.","Jané","http://forum.jumeaux-et-plus.fr/topic,33018.0","高"))
rows.append(r("法国","西欧高信任论坛区","家居出行","垂类社区类","CommentReparer","体验","产品损坏/质量缺陷","Roue avant Chicco poussette cassée. Pièce plastique de la roue fissurée et roue ne tourne plus correctement. Pas de pièce détachée disponible chez le fabricant.","Chicco","https://www.commentreparer.com/75931/Chicco","中"))

# === 西语区 (西班牙/墨西哥) ===
rows.append(r("西班牙","南欧拉美社媒区","家居出行","垂类官方媒体类","OCU","安全","产品损坏/质量缺陷","ALERTA OCU: Silla de coche Peg Perego Viaggio Twist - defecto grave de seguridad. En choque frontal la pieza de sujeción se rompe y el asiento se desprende. Dejar de usar inmediatamente.","Peg Perego","https://www.diariodenavarra.es/noticias/vivir/consumo/2024/04/18/ocu-sillita-insegura-605700.html","高"))
rows.append(r("西班牙","南欧拉美社媒区","家居出行","垂类社区类","Cotilleando","安全","产品损坏/质量缺陷","Bugaboo Dragonfly recall por fallo en respaldo que se reclina de forma peligrosa. Modelos anteriores a junio 2023 afectados. Riesgo de caída del bebé.","Bugaboo","https://www.cotilleando.com/threads/cochecitos-experiencias.144705/page-258","高"))
rows.append(r("墨西哥","南欧拉美社媒区","家居出行","垂类社区类","Consumidores MX","体验","产品损坏/质量缺陷","Carriola Graco en México: Reportes de problemas con ruedas que se traban, sistema de plegado que se atora, y materiales que se desgastan rápidamente con uso normal.","Graco","https://consumidores.com.mx/b/carriolas-graco/","中"))

print(f"Total new rows: {len(rows)}")

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
cd = {}; ld = {}; bd = {}; pd = {}
for rec in deduped:
    c = rec["国家"]; cd[c] = cd.get(c, 0) + 1
    l = rec["产品品线"]; ld[l] = ld.get(l, 0) + 1
    b = rec["竞品关联品牌"] or "未指定"; bd[b] = bd.get(b, 0) + 1
    p = rec["平台"]; pd[p] = pd.get(p, 0) + 1

# Save staging
STAGING.parent.mkdir(parents=True, exist_ok=True)
with open(STAGING, "w", encoding="utf-8") as f:
    json.dump({"batch": BATCH, "total": len(deduped), "country": cd, "line": ld, "brand": bd, "platform": pd}, f, ensure_ascii=False, indent=2)

# Append
with open(TARGET, "a", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writerows(deduped)

print(f"Appended {len(deduped)} rows to CSV")
print(f"Countries: {cd}")
print(f"Lines: {ld}")
print(f"Brands: {bd}")
print(f"Platforms: {pd}")
