# -*- coding: utf-8 -*-
"""清洗 voc_summary_persona_flat.csv → voc_persona_summary section。"""
from __future__ import annotations
from ._common import (
    read_csv_table, clean_str, clean_num, clean_int, get_code,
    normalize_product_line, normalize_platform_type, infer_platform_type_from_name, TABLES_DIR,
)


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "voc_summary_persona_flat.csv")
    result = []
    for r in rows:
        country = clean_str(r.get("国家"))
        if not country:
            continue
        total = clean_int(r.get("有效评论数")) or 0
        neg = clean_int(r.get("负向数")) or 0
        platform = clean_str(r.get("平台")) or clean_str(r.get("涉及平台列表"))
        platform_type_raw = clean_str(r.get("平台类型"))
        platform_type = normalize_platform_type(platform_type_raw) if platform_type_raw else infer_platform_type_from_name(platform)
        result.append({
            "country": country,
            "country_code": get_code(country),
            "cluster": clean_str(r.get("区域cluster")),
            "product_line": normalize_product_line(r.get("产品品线")),
            "platform_type": platform_type,
            "platform": platform,
            "segment_code": clean_str(r.get("画像编码")),
            "segment_name": clean_str(r.get("画像名称")),
            "lifecycle": clean_str(r.get("生命周期")),
            "content_cnt": clean_int(r.get("内容数")),
            "valid_comment_cnt": total,
            "positive_cnt": clean_int(r.get("正向数")),
            "negative_cnt": neg,
            "neutral_cnt": clean_int(r.get("中性数")),
            "negative_rate": round(neg / total * 100, 1) if total > 0 else 0,
            "top3_negative": clean_str(r.get("TOP3负面主题")),
            "top3_positive": clean_str(r.get("TOP3正面主题")),
            "top3_competitors": clean_str(r.get("TOP3竞品提及")),
            "collect_start": clean_str(r.get("采集时间起")),
            "collect_end": clean_str(r.get("采集时间止")),
            "batch_code": clean_str(r.get("批次编码")),
            "data_quality": clean_str(r.get("数据质量(A/B/C)")) or "C",
        })
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
