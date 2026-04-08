# -*- coding: utf-8 -*-
"""清洗 dim_voc_negative_extract.csv → voc_negative section。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, clean_int, get_code,
    normalize_product_line, normalize_platform_type, normalize_brand,
    infer_pain_subcategory, is_chinese_text, PAIN_SUBCATEGORY_PARENT,
    get_default_segment,
    TABLES_DIR,
)

PAIN_CATEGORIES = {"功能", "价格", "体验", "服务", "安全"}
INTENSITY_VALUES = {"高", "中", "低"}


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_voc_negative_extract.csv")
    result = []
    seen_keys: set[str] = set()
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue

        url = clean_str(r.get("来源URL")) or ""
        original_text = (clean_str(r.get("负面原文摘录(本地语言)")) or "")[:600]
        text_prefix = original_text[:50]
        dedup_key = f"{url}||{text_prefix}"
        if dedup_key in seen_keys:
            print(f"  WARN: duplicate skipped: {url[:60]}  text: {text_prefix[:30]}")
            continue
        seen_keys.add(dedup_key)

        pain_cat = clean_str(r.get("痛点大类(功能/价格/体验/服务/安全)")) or "体验"
        if pain_cat not in PAIN_CATEGORIES:
            pain_cat = "体验"

        intensity = clean_str(r.get("负面强度(高/中/低)")) or "中"
        if intensity not in INTENSITY_VALUES:
            intensity = "中"

        product_line = normalize_product_line(r.get("产品品线"))
        neg_theme = clean_str(r.get("负面主题")) or ""

        subcat = infer_pain_subcategory(product_line, original_text, neg_theme)
        if subcat != "其他" and subcat in PAIN_SUBCATEGORY_PARENT:
            pain_cat = PAIN_SUBCATEGORY_PARENT[subcat]

        if not neg_theme and subcat != "其他":
            neg_theme = subcat

        brand = normalize_brand(r.get("竞品关联品牌"))

        translated = clean_str(r.get("负面原文摘录(中文翻译)"))
        if translated and not is_chinese_text(translated):
            translated = None
        if translated:
            translated = translated[:300]

        segment_code = clean_str(r.get("画像编码"))
        segment_name = clean_str(r.get("画像名称"))
        lifecycle = clean_str(r.get("生命周期"))
        if not segment_code or not segment_name or not lifecycle:
            segment_code, segment_name, lifecycle = get_default_segment(product_line)

        result.append({
            "country": country,
            "country_code": get_code(country),
            "cluster": clean_str(r.get("区域cluster")),
            "product_line": product_line,
            "platform_type": normalize_platform_type(r.get("平台类型")),
            "platform": clean_str(r.get("平台")),
            "segment_code": segment_code,
            "segment_name": segment_name,
            "lifecycle": lifecycle,
            "pain_category": pain_cat,
            "pain_subcategory": subcat,
            "negative_theme": neg_theme or None,
            "original_text": original_text,
            "translated_text": translated,
            "frequency": clean_int(r.get("频次估算")),
            "intensity": intensity,
            "competitor_brand": brand,
            "action_suggestion": clean_str(r.get("对应运营建议")),
            "source_url": url,
            "collect_date": clean_str(r.get("采集日期")),
            "batch_code": clean_str(r.get("批次编码")),
            "priority": clean_str(r.get("优先级")) or "P2",
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    subcats = {}
    for row in data:
        sc = row.get("pain_subcategory", "其他")
        subcats[sc] = subcats.get(sc, 0) + 1
    print("Subcategory distribution:")
    for k, v in sorted(subcats.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    brands_missing_theme = sum(1 for row in data if not row.get("negative_theme"))
    print(f"Missing negative_theme: {brands_missing_theme}")
    non_chinese_translated = sum(1 for row in data if row.get("translated_text") and not is_chinese_text(row["translated_text"]))
    print(f"Non-Chinese in translated_text (should be 0): {non_chinese_translated}")
