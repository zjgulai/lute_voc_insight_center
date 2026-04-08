#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 Momcozy 内部 VOC 差评明细 xlsx 聚合后接入 dim_voc_negative_extract.csv。

设计原则：
1. 保留主表标准 20 列，走现有 export_viz_json 链路。
2. 由于源表为 10w+ 明细，不直接逐条下发到前端，而是按关键维度聚合。
3. 每个聚合组保留一条代表性原文，频次写入「频次估算」。
4. 生成 staging 审计文件，便于复跑与核对。
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ))

from tools.cleaning._common import infer_pain_subcategory, PAIN_SUBCATEGORY_PARENT

SOURCE_XLSX = PROJ / "data" / "add_data" / "VOC差评_SPU关联_星级lt3_合并原文_20260408_040101.xlsx"
TARGET_CSV = PROJ / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
STAGING_DIR = PROJ / "data" / "processed"
CSV_20_HEADERS = [
    "国家", "区域cluster", "产品品线", "平台类型", "平台",
    "画像编码", "画像名称", "生命周期", "痛点大类(功能/价格/体验/服务/安全)",
    "负面主题", "负面原文摘录(本地语言)", "负面原文摘录(中文翻译)",
    "频次估算", "负面强度(高/中/低)", "竞品关联品牌", "对应运营建议",
    "来源URL", "采集日期", "批次编码", "优先级",
]

BATCH_CODE = f"MOMCOZY-INTERNAL-{datetime.now().strftime('%Y%m%d')}"

COUNTRY_CLUSTER = {
    "美国": "北美高购买力区",
    "加拿大": "北美高购买力区",
    "英国": "西欧高信任论坛区",
    "德国": "西欧高信任论坛区",
    "法国": "西欧高信任论坛区",
    "荷兰": "西欧高信任论坛区",
    "比利时": "西欧高信任论坛区",
    "奥地利": "西欧高信任论坛区",
    "瑞士": "西欧高信任论坛区",
    "爱尔兰": "西欧高信任论坛区",
    "瑞典": "西欧高信任论坛区",
    "挪威": "西欧高信任论坛区",
    "芬兰": "西欧高信任论坛区",
    "波兰": "中东欧价格敏感区",
    "罗马尼亚": "中东欧价格敏感区",
    "匈牙利": "中东欧价格敏感区",
    "西班牙": "南欧拉美社媒区",
    "意大利": "南欧拉美社媒区",
    "葡萄牙": "南欧拉美社媒区",
    "墨西哥": "南欧拉美社媒区",
    "秘鲁": "南欧拉美社媒区",
    "澳大利亚": "英语口碑圈",
    "新加坡": "东南亚城市中产区",
    "马来西亚": "东南亚城市中产区",
    "沙特阿拉伯": "中东视觉社媒区",
    "阿联酋": "中东视觉社媒区",
}

SEGMENT_BY_LINE = {
    "吸奶器": ("SEG01", "产后建奶新手妈妈", "产后0-6月"),
    "喂养电器": ("SEG02", "精细喂养效率型妈妈", "0-12月"),
    "家居出行": ("SEG03", "出行场景育儿家庭", "孕晚期-24月"),
    "内衣服饰": ("SEG04", "孕产护理妈妈", "孕期-产后6月"),
    "护理电器": ("SEG05", "清洁护理妈妈", "0-12月"),
    "母婴综合护理": ("SEG06", "综合护理家庭", "孕期-24月"),
    "智能母婴电器": ("SEG07", "智能育儿家庭", "0-24月"),
}

PLATFORM_LABEL_MAP = {
    "独立站": ("竞品官方电商", "Momcozy独立站"),
    "亚马逊": ("电商平台", "Amazon"),
    "国内": ("电商平台", "Tmall/JD"),
    "新平台": ("电商平台", "新平台"),
    "Tiktok平台": ("社媒传播类", "TikTok Shop"),
    "线下": ("第三方评测类", "线下售后"),
}

SERVICE_LABEL_PARTS = [
    "物流", "发货", "退货", "退款", "取消", "订单", "售后", "缺货",
    "包裹", "收件", "丢包", "到达未收到",
]
PRICE_LABEL_PARTS = ["价格", "支付", "费用", "折扣", "优惠"]
SAFETY_LABEL_PARTS = ["熔化", "冒烟", "气味", "异味", "破损", "断裂", "卡扣破损"]
FUNCTION_LABEL_PARTS = [
    "吸力", "无法开机", "无法关机", "充不进电", "耗电", "续航",
    "按键故障", "显示故障", "错误代码", "无法加热", "缺水报错",
    "奇怪的声音", "没有吸力",
]

LOW_SIGNAL_PATTERNS = [
    re.compile(r"^Conversation with(?: Web User)?\s+.+$", re.I),
    re.compile(r"^Call from:", re.I),
    re.compile(r"请在客户端查看原始聊天记录", re.I),
]


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\ufeff", "")
    return text


def is_low_signal(text: str) -> bool:
    if not text:
        return True
    return any(p.search(text) for p in LOW_SIGNAL_PATTERNS)


def normalize_country(value: object) -> str:
    country = clean_text(value)
    country = country.replace("(中国)香港", "中国香港").replace("(中国)澳门", "中国澳门")
    if country == "香港":
        country = "中国香港"
    if country == "澳门":
        country = "中国澳门"
    if not country or country == "未匹配":
        return ""
    return country


def normalize_line(value: object) -> str:
    line = clean_text(value)
    if line in {"母婴电器创新", "孕产康产品部"}:
        return ""
    return line


def normalize_date(value: object) -> str:
    if value is None or pd.isna(value):
        return datetime.now().strftime("%Y-%m-%d")
    try:
        ts = pd.to_datetime(value)
        if pd.isna(ts):
            return datetime.now().strftime("%Y-%m-%d")
        return ts.strftime("%Y-%m-%d")
    except Exception:
        text = clean_text(value)
        return text[:10] if text else datetime.now().strftime("%Y-%m-%d")


def normalize_platform(platform_name: object, channel_name: object) -> tuple[str, str]:
    platform = clean_text(platform_name)
    channel = clean_text(channel_name).lower()
    if channel == "shopify":
        return "竞品官方电商", "Momcozy独立站"
    if channel == "tiktok":
        return "社媒传播类", "TikTok Shop"
    if channel in {
        "amazon", "amazon-vc", "walmart", "bestbuy", "noon", "ebay", "shopee",
        "cdiscount", "shein", "worten", "lazada", "aliexpress", "catch", "temu",
        "tmall", "jd", "mercadocbt",
    }:
        return "电商平台", channel.title()
    if platform in PLATFORM_LABEL_MAP:
        return PLATFORM_LABEL_MAP[platform]
    return "电商平台", channel.title() if channel else platform or "未知平台"


def infer_pain_category(label: str, text: str, product_line: str) -> str:
    combined = f"{label} {text}".lower()
    if any(part in label for part in PRICE_LABEL_PARTS):
        return "价格"
    if any(part in label for part in SERVICE_LABEL_PARTS):
        return "服务"
    if any(part in label for part in SAFETY_LABEL_PARTS):
        return "安全"
    if any(part in label for part in FUNCTION_LABEL_PARTS):
        return "功能"

    subcat = infer_pain_subcategory(product_line, text, label)
    if subcat in PAIN_SUBCATEGORY_PARENT:
        return PAIN_SUBCATEGORY_PARENT[subcat]
    if "refund" in combined or "return" in combined or "warranty" in combined:
        return "服务"
    if "price" in combined or "expensive" in combined:
        return "价格"
    if "burn" in combined or "smell" in combined or "crack" in combined:
        return "安全"
    if "suction" in combined or "heat" in combined or "power" in combined:
        return "功能"
    return "体验"


def infer_intensity(label: str, text: str, frequency: int) -> str:
    combined = f"{label} {text}".lower()
    if frequency >= 20:
        return "高"
    if any(word in combined for word in ["strong dissatisfaction", "highly disappointed", "refund", "冒烟", "burnt", "physical pain"]):
        return "高"
    if frequency >= 5:
        return "中"
    return "低"


def stable_source_url(country: str, line: str, platform: str, label: str, date: str) -> str:
    key = "|".join([country, line, platform, label, date])
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]
    return f"internal://momcozy-negative/{digest}"


def best_text(values: pd.Series) -> str:
    candidates = [clean_text(v) for v in values.tolist()]
    candidates = [t for t in candidates if t and not is_low_signal(t)]
    if not candidates:
        return ""
    candidates.sort(key=lambda x: (len(x), x.count("\n")), reverse=True)
    return candidates[0][:4000]


def build_rows(df: pd.DataFrame) -> list[dict]:
    required = [
        "产品品线", "VOC产生日期", "平台名称", "渠道名称",
        "国家名称", "VOC标签", "客户原文_合并",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"源文件缺少列: {missing}")

    work = df.copy()
    work["产品品线"] = work["产品品线"].map(normalize_line)
    work["国家名称"] = work["国家名称"].map(normalize_country)
    work["VOC产生日期"] = work["VOC产生日期"].map(normalize_date)
    work["VOC标签"] = work["VOC标签"].map(clean_text)
    work["客户原文_合并"] = work["客户原文_合并"].map(clean_text)
    work = work[
        (work["产品品线"] != "") &
        (work["国家名称"] != "") &
        (work["VOC标签"] != "") &
        (work["客户原文_合并"] != "")
    ].copy()

    grouped = (
        work.groupby(["国家名称", "产品品线", "平台名称", "渠道名称", "VOC标签"], dropna=False)
        .agg(
            采集日期=("VOC产生日期", "max"),
            代表原文=("客户原文_合并", best_text),
            频次估算=("客户原文_合并", "size"),
        )
        .reset_index()
    )

    rows: list[dict] = []
    for _, item in grouped.iterrows():
        country = str(item["国家名称"])
        line = str(item["产品品线"])
        label = str(item["VOC标签"])
        collect_date = str(item["采集日期"])
        frequency = int(item["频次估算"])
        original_text = clean_text(item["代表原文"])
        if not original_text or is_low_signal(original_text) or len(original_text) < 20:
            continue

        platform_type_label, platform = normalize_platform(item["平台名称"], item["渠道名称"])
        pain_category = infer_pain_category(label, original_text, line)
        intensity = infer_intensity(label, original_text, frequency)
        segment_code, segment_name, lifecycle = SEGMENT_BY_LINE.get(
            line, ("SEG99", "综合育儿用户", "孕期-24月")
        )

        rows.append({
            "国家": country,
            "区域cluster": COUNTRY_CLUSTER.get(country, "其他区域"),
            "产品品线": line,
            "平台类型": platform_type_label,
            "平台": platform,
            "画像编码": segment_code,
            "画像名称": segment_name,
            "生命周期": lifecycle,
            "痛点大类(功能/价格/体验/服务/安全)": pain_category,
            "负面主题": label[:100],
            "负面原文摘录(本地语言)": original_text[:4000],
            "负面原文摘录(中文翻译)": "",
            "频次估算": str(frequency),
            "负面强度(高/中/低)": intensity,
            "竞品关联品牌": "Momcozy",
            "对应运营建议": "",
            "来源URL": stable_source_url(country, line, platform, label, collect_date),
            "采集日期": collect_date,
            "批次编码": BATCH_CODE,
            "优先级": "P1" if frequency >= 5 else "P2",
        })
    return rows


def dedup_against_existing(rows: list[dict]) -> list[dict]:
    existing_keys: set[str] = set()
    if TARGET_CSV.exists():
        with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = (row.get("来源URL") or "").strip()
                text_prefix = (row.get("负面原文摘录(本地语言)") or "")[:50]
                existing_keys.add(f"{url}||{text_prefix}")

    deduped: list[dict] = []
    new_keys: set[str] = set()
    for row in rows:
        url = row.get("来源URL", "")
        text_prefix = row.get("负面原文摘录(本地语言)", "")[:50]
        key = f"{url}||{text_prefix}"
        if key in existing_keys or key in new_keys:
            continue
        new_keys.add(key)
        deduped.append(row)
    print(f"Dedup: {len(rows)} -> {len(deduped)} (removed {len(rows) - len(deduped)})")
    return deduped


def save_staging(rows: list[dict], source_rows: int) -> Path:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    path = STAGING_DIR / f"momcozy_internal_ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "batch_code": BATCH_CODE,
        "source_xlsx": str(SOURCE_XLSX),
        "source_rows": source_rows,
        "final_rows": len(rows),
        "country_distribution": dict(Counter(r["国家"] for r in rows).most_common(30)),
        "product_line_distribution": dict(Counter(r["产品品线"] for r in rows).most_common(30)),
        "platform_distribution": dict(Counter(r["平台"] for r in rows).most_common(30)),
        "pain_category_distribution": dict(Counter(r["痛点大类(功能/价格/体验/服务/安全)"] for r in rows).most_common(30)),
        "top_theme_distribution": dict(Counter(r["负面主题"] for r in rows).most_common(50)),
        "sample_rows": rows[:20],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def append_to_csv(rows: list[dict]) -> None:
    file_exists = TARGET_CSV.exists() and TARGET_CSV.stat().st_size > 0
    with open(TARGET_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_20_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    if not SOURCE_XLSX.exists():
        raise FileNotFoundError(f"源文件不存在: {SOURCE_XLSX}")

    print("=== Momcozy Internal XLSX Ingest ===")
    print(f"Source: {SOURCE_XLSX}")
    print(f"Target: {TARGET_CSV}")
    print(f"Batch:  {BATCH_CODE}")
    print(f"Mode:   {'DRY RUN' if dry_run else 'LIVE'}")

    df = pd.read_excel(SOURCE_XLSX)
    source_rows = len(df)
    rows = build_rows(df)
    rows = dedup_against_existing(rows)
    staging_path = save_staging(rows, source_rows)

    print(f"Source rows: {source_rows}")
    print(f"Final rows : {len(rows)}")
    print(f"Staging    : {staging_path}")
    if rows:
        print("Top countries:", dict(Counter(r["国家"] for r in rows).most_common(10)))
        print("Top lines   :", dict(Counter(r["产品品线"] for r in rows).most_common(10)))
        print("Top pains   :", dict(Counter(r["痛点大类(功能/价格/体验/服务/安全)"] for r in rows).most_common(10)))

    if dry_run:
        print("[DRY RUN] Skip CSV append.")
        return

    append_to_csv(rows)
    print(f"Appended {len(rows)} rows to {TARGET_CSV}")


if __name__ == "__main__":
    main()
