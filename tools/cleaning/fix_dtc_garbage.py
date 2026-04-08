# -*- coding: utf-8 -*-
"""
fix_dtc_garbage.py — 一次性清洗脚本：
  1. 识别并删除 DTC/社区采集中的垃圾行（Cloudflare 页面、404 错误、markdown 残片等）
  2. 补全有效行的缺失字段（画像编码、生命周期、频次估算）
  3. 输出清洗后的 CSV + 删除日志

用法:
    python tools/cleaning/fix_dtc_garbage.py
"""
from __future__ import annotations

import csv
import io
import re
import sys
from datetime import datetime
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
CSV_PATH = PROJ / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
LOG_PATH = PROJ / "tools" / "cleaning" / "output" / "fix_dtc_garbage_log.txt"

GARBAGE_PATTERNS = [
    re.compile(r"Cloudflare", re.IGNORECASE),
    re.compile(r"Target URL returned error", re.IGNORECASE),
    re.compile(r"CAPTCHA", re.IGNORECASE),
    re.compile(r"email the site owner", re.IGNORECASE),
    re.compile(r"^Title:\s*(404|Something went wrong|Attention Required)", re.IGNORECASE),
    re.compile(r"^Warning:\s*Target URL returned error"),
    re.compile(r"^URL Source:\s*https?://"),
    re.compile(r"^Markdown Content:\s*#?\s*\w"),
    re.compile(r"^\]\(https?://"),
    re.compile(r"^!\[Image\s+\d+\]"),
    re.compile(r"Reasons Your Baby Won.t Sleep", re.IGNORECASE),
    re.compile(r"Toddler Refuses to Poop", re.IGNORECASE),
    re.compile(r"^Please specify a reason for deleting"),
    re.compile(r"^Shopping online\s*\*"),
    re.compile(r"^Support Support\s*\*"),
    re.compile(r"^Join the conversation\s*\*"),
    re.compile(r"^\*\s+\*\s+\*\s+\*\s+\*"),
    re.compile(r"^Heading to the\s+\*"),
    re.compile(r"^Top mentions\s+Customer service"),
    re.compile(r"30.Day.+Return Policy", re.IGNORECASE),
    re.compile(r"^30 Days Guarantee"),
    re.compile(r"Non-Quality Issues\*\*"),
    re.compile(r"Quality Issues\*\*.*warranty period"),
    re.compile(r"^It.s better to buy on babybrezza\.com"),
    re.compile(r"Buy and try for 100 days"),
    re.compile(r"Bugaboo Dragonfly The future city stroller"),
    re.compile(r"Why choose Bugaboo"),
    re.compile(r"stars\.\s*\d+ reviews \[View product\]"),
    re.compile(r"Workplace friendly discretion Continue to feed"),
]

SEGMENT_MAP = {
    "吸奶器": ("SEG01", "产后建奶新手妈妈", "产后0-6月"),
    "喂养电器": ("SEG03", "效率至上职场妈妈", "产后3-12月"),
    "家居出行": ("SEG05", "品质生活追求者", "孕期-学龄前"),
    "智能监控": ("SEG05", "品质生活追求者", "产后0-12月"),
    "消毒柜": ("SEG03", "效率至上职场妈妈", "产后0-12月"),
    "暖奶器": ("SEG03", "效率至上职场妈妈", "产后0-6月"),
    "辅食机": ("SEG04", "辅食探索妈妈", "产后6-24月"),
}

COMMUNITY_BATCH_MARKERS = ["COMMUNITY", "社区"]
DTC_BATCH_MARKERS = ["DTC", "竞品官方电商"]

log_lines: list[str] = []


def log(msg: str):
    log_lines.append(msg)
    try:
        print(msg)
    except Exception:
        pass


def is_garbage(text: str) -> str | None:
    """Return reason string if text is garbage, None if valid."""
    if not text or len(text.strip()) < 15:
        return "too_short"
    stripped = text.strip()
    for pat in GARBAGE_PATTERNS:
        if pat.search(stripped):
            return f"pattern:{pat.pattern[:40]}"
    alpha_count = sum(1 for c in stripped if c.isalpha())
    if alpha_count < 10:
        return "too_few_letters"
    return None


def is_not_negative(text: str) -> bool:
    """Check if content is clearly positive / not a real negative review."""
    lower = text.lower()
    positive_only = [
        "great. just what i need",
        "love love love",
        "convenient and effective",
        "amazing product",
    ]
    for p in positive_only:
        if lower.startswith(p):
            neg_kw = ["but", "however", "issue", "problem", "leak", "broke", "disappoint",
                       "defect", "unfortunately", "worst", "terrible"]
            if not any(k in lower for k in neg_kw):
                return True
    return False


def fill_missing(row: dict) -> dict:
    """Fill empty persona/lifecycle/frequency fields with heuristic defaults."""
    product_line = row.get("产品品线", "").strip()
    batch = row.get("批次编码", "")

    if not row.get("画像编码", "").strip() and product_line in SEGMENT_MAP:
        seg_code, seg_name, lifecycle = SEGMENT_MAP[product_line]
        row["画像编码"] = seg_code
        row["画像名称"] = seg_name
        if not row.get("生命周期", "").strip():
            row["生命周期"] = lifecycle

    if not row.get("频次估算", "").strip():
        is_community = any(m in batch for m in COMMUNITY_BATCH_MARKERS)
        row["频次估算"] = "3" if is_community else "1"

    return row


def main():
    if not CSV_PATH.exists():
        log(f"ERROR: {CSV_PATH} not found")
        sys.exit(1)

    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    log(f"Input: {len(rows)} rows")

    kept: list[dict] = []
    removed: list[tuple[int, str, str]] = []

    for i, row in enumerate(rows):
        text = row.get("负面原文摘录(本地语言)", "").strip()
        reason = is_garbage(text)
        if reason:
            removed.append((i + 2, reason, text[:80]))
            continue
        if is_not_negative(text):
            removed.append((i + 2, "positive_content", text[:80]))
            continue
        kept.append(fill_missing(row))

    log(f"Kept: {len(kept)} rows")
    log(f"Removed: {len(removed)} rows")
    log("")

    for line_no, reason, snippet in removed:
        log(f"  DEL line {line_no}: [{reason}] {snippet}")

    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    log(f"\nOutput: {CSV_PATH} ({len(kept)} rows)")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"fix_dtc_garbage.py — {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n")
        f.write("\n".join(log_lines))

    log(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()
