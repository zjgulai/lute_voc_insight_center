"""
P4: Generate structured summary report for VOC negative data.
Writes output to a markdown file to avoid console encoding issues.
"""
import csv
from collections import Counter
from pathlib import Path
from datetime import datetime

CSV = Path(r'd:\专题2：VOC分析\voc-data-product\data\delivery\tables\dim_voc_negative_extract.csv')
REPORT = Path(r'd:\专题2：VOC分析\voc-data-product\data\delivery\tables\voc_negative_summary_report.md')

with open(CSV, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fns = reader.fieldnames
    rows = list(reader)

lines = []
lines.append(f"# VOC 负面数据采集汇总报告")
lines.append(f"")
lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append(f"**总记录数**: {len(rows)}")
lines.append(f"**数据字段**: {len(fns)}")
lines.append(f"")

lines.append("## 1. 字段填充率")
lines.append("")
lines.append("| 字段 | 填充率 | 唯一值数 |")
lines.append("|------|--------|----------|")
labels = [
    '国家', '区域cluster', '产品品线', '平台类型', '平台',
    '画像编码', '画像名称', '生命周期',
    '痛点大类', '负面主题', '负面原文摘录(本地语言)', '负面原文摘录(中文翻译)',
    '频次估算', '负面强度', '竞品关联品牌', '对应运营建议',
    '来源URL', '采集日期', '批次编码', '优先级',
]
for i, label in enumerate(labels):
    if i >= len(fns):
        break
    key = fns[i]
    vals = [row[key] for row in rows]
    non_empty = sum(1 for v in vals if v.strip())
    fill_pct = non_empty / len(rows) * 100
    unique = len(set(v for v in vals if v.strip()))
    lines.append(f"| {label} | {fill_pct:.1f}% | {unique} |")

lines.append("")
lines.append("## 2. 品牌分布")
lines.append("")
lines.append("| 品牌 | 数量 | 占比 |")
lines.append("|------|------|------|")
brand_key = fns[14]
c = Counter(row[brand_key] for row in rows)
for v, cnt in c.most_common(20):
    pct = cnt / len(rows) * 100
    lines.append(f"| {v or '(空)'} | {cnt} | {pct:.1f}% |")

lines.append("")
lines.append("## 3. 产品品线分布")
lines.append("")
lines.append("| 品线 | 数量 | 占比 |")
lines.append("|------|------|------|")
c = Counter(row[fns[2]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    lines.append(f"| {v} | {cnt} | {pct:.1f}% |")

lines.append("")
lines.append("## 4. 国家分布")
lines.append("")
lines.append("| 国家 | 数量 | 占比 |")
lines.append("|------|------|------|")
c = Counter(row[fns[0]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    lines.append(f"| {v} | {cnt} | {pct:.1f}% |")

lines.append("")
lines.append("## 5. 痛点大类分布")
lines.append("")
lines.append("| 痛点大类 | 数量 | 占比 |")
lines.append("|----------|------|------|")
c = Counter(row[fns[8]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    lines.append(f"| {v} | {cnt} | {pct:.1f}% |")

lines.append("")
lines.append("## 6. 负面强度分布")
lines.append("")
lines.append("| 强度 | 数量 | 占比 |")
lines.append("|------|------|------|")
c = Counter(row[fns[13]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    lines.append(f"| {v} | {cnt} | {pct:.1f}% |")

lines.append("")
lines.append("## 7. Top 20 负面主题")
lines.append("")
lines.append("| 负面主题 | 数量 | 占比 |")
lines.append("|----------|------|------|")
c = Counter(row[fns[9]] for row in rows)
for v, cnt in c.most_common(20):
    pct = cnt / len(rows) * 100
    lines.append(f"| {v} | {cnt} | {pct:.1f}% |")

lines.append("")
lines.append("## 8. 品牌×痛点交叉分析")
lines.append("")
pain_cats = sorted(set(row[fns[8]] for row in rows))
header = "| 品牌 | " + " | ".join(pain_cats) + " | 合计 |"
sep = "|------|" + "|".join(["------"] * len(pain_cats)) + "|------|"
lines.append(header)
lines.append(sep)
brands = Counter(row[brand_key] for row in rows)
for brand, total in brands.most_common(15):
    brand_rows = [r for r in rows if r[brand_key] == brand]
    pain_counts = Counter(r[fns[8]] for r in brand_rows)
    cells = [str(pain_counts.get(pc, 0)) for pc in pain_cats]
    lines.append(f"| {brand or '(空)'} | " + " | ".join(cells) + f" | {total} |")

lines.append("")
lines.append("## 9. 采集批次汇总")
lines.append("")
lines.append("| 批次编码 | 数量 |")
lines.append("|----------|------|")
c = Counter(row[fns[18]] for row in rows)
for v, cnt in c.most_common():
    lines.append(f"| {v} | {cnt} |")

lines.append("")
lines.append("---")
lines.append("*报告自动生成，数据来源：dim_voc_negative_extract.csv*")

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"[P4] Report written to {REPORT}")
print(f"[P4] Total lines: {len(lines)}")
