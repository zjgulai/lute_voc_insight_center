"""
P4 脚本 — 四维汇总：dim_voc_negative_extract → voc_summary_persona_flat

功能：
  1. 从 dim_voc_negative_extract.csv 读取全量负面 VOC 条目
  2. 按 国家 × 品线 × 画像 × 痛点大类 四维分组汇总
  3. 生成 voc_summary_persona_flat.csv（四维汇总表）
  4. 同步更新 voc_summary_flat.csv（国家×品线 二维汇总）
  5. 输出汇总统计报告

写入：
  data/delivery/tables/voc_summary_persona_flat.csv
  data/delivery/tables/voc_summary_flat.csv
  tools/collect/output/p4_rollup_report.txt
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
PERSONA_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "voc_summary_persona_flat.csv"
SUMMARY_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "voc_summary_flat.csv"
OUTPUT_DIR = Path(__file__).parent / "output"

PERSONA_FIELDS = [
    "国家", "区域cluster", "产品品线",
    "画像编码", "画像名称", "生命周期",
    "痛点大类", "负面主题TOP3", "典型原文摘要",
    "条目数", "高强度占比", "涉及平台数", "涉及平台列表",
    "竞品品牌TOP3", "平均质量分",
    "汇总日期", "覆盖批次",
]

SUMMARY_FIELDS = [
    "国家", "区域cluster", "产品品线",
    "负面主题TOP5", "总条目数",
    "功能占比", "价格占比", "体验占比", "服务占比", "安全占比",
    "高强度占比", "涉及画像数", "涉及平台数",
    "竞品品牌TOP3", "汇总日期",
]


def load_extract() -> list[dict]:
    if not SRC_CSV.exists():
        print(f"[错误] {SRC_CSV} 不存在")
        return []
    with open(SRC_CSV, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def rollup_persona(rows: list[dict]) -> list[dict]:
    """四维分组: 国家 × 品线 × 画像 × 痛点"""
    groups: dict[tuple, list[dict]] = defaultdict(list)

    for r in rows:
        key = (
            r.get("国家", ""),
            r.get("区域cluster", ""),
            r.get("产品品线", ""),
            r.get("画像编码", ""),
            r.get("画像名称", ""),
            r.get("生命周期", ""),
            r.get("痛点大类(功能/价格/体验/服务/安全)", ""),
        )
        groups[key].append(r)

    output = []
    for key, items in sorted(groups.items()):
        country, cluster, line, seg_code, seg_name, lifecycle, pain = key

        themes = Counter()
        competitors = Counter()
        platforms = set()
        batches = set()
        high_count = 0
        originals = []

        for item in items:
            theme = item.get("负面主题", "").strip()
            if theme:
                themes[theme] += 1

            comp = item.get("竞品关联品牌", "").strip()
            if comp:
                for c in comp.split(";"):
                    c = c.strip()
                    if c:
                        competitors[c] += 1

            plat = item.get("平台", "").strip()
            if plat:
                platforms.add(plat)

            batch = item.get("批次编码", "").strip()
            if batch:
                batches.add(batch)

            if item.get("负面强度(高/中/低)", "") == "高":
                high_count += 1

            orig = item.get("负面原文摘录(本地语言)", "").strip()
            if orig and len(originals) < 3:
                originals.append(orig[:80])

        top3_themes = "; ".join([t for t, _ in themes.most_common(3)])
        top3_comp = "; ".join([c for c, _ in competitors.most_common(3)])
        high_pct = f"{high_count/len(items)*100:.0f}%" if items else "0%"

        output.append({
            "国家": country,
            "区域cluster": cluster,
            "产品品线": line,
            "画像编码": seg_code,
            "画像名称": seg_name,
            "生命周期": lifecycle,
            "痛点大类": pain,
            "负面主题TOP3": top3_themes,
            "典型原文摘要": " | ".join(originals),
            "条目数": len(items),
            "高强度占比": high_pct,
            "涉及平台数": len(platforms),
            "涉及平台列表": "; ".join(sorted(platforms)),
            "竞品品牌TOP3": top3_comp,
            "平均质量分": "",
            "汇总日期": str(date.today()),
            "覆盖批次": "; ".join(sorted(batches)),
        })

    return output


def rollup_summary(rows: list[dict]) -> list[dict]:
    """二维分组: 国家 × 品线"""
    groups: dict[tuple, list[dict]] = defaultdict(list)

    for r in rows:
        key = (
            r.get("国家", ""),
            r.get("区域cluster", ""),
            r.get("产品品线", ""),
        )
        groups[key].append(r)

    output = []
    for key, items in sorted(groups.items()):
        country, cluster, line = key

        themes = Counter()
        pain_counter = Counter()
        competitors = Counter()
        platforms = set()
        personas = set()
        high_count = 0

        for item in items:
            theme = item.get("负面主题", "").strip()
            if theme:
                themes[theme] += 1

            pain = item.get("痛点大类(功能/价格/体验/服务/安全)", "").strip()
            if pain:
                pain_counter[pain] += 1

            comp = item.get("竞品关联品牌", "").strip()
            if comp:
                for c in comp.split(";"):
                    if c.strip():
                        competitors[c.strip()] += 1

            plat = item.get("平台", "").strip()
            if plat:
                platforms.add(plat)

            seg = item.get("画像编码", "").strip()
            if seg:
                personas.add(seg)

            if item.get("负面强度(高/中/低)", "") == "高":
                high_count += 1

        n = len(items)
        top5_themes = "; ".join([t for t, _ in themes.most_common(5)])
        top3_comp = "; ".join([c for c, _ in competitors.most_common(3)])

        output.append({
            "国家": country,
            "区域cluster": cluster,
            "产品品线": line,
            "负面主题TOP5": top5_themes,
            "总条目数": n,
            "功能占比": f"{pain_counter.get('功能', 0)/n*100:.0f}%" if n else "0%",
            "价格占比": f"{pain_counter.get('价格', 0)/n*100:.0f}%" if n else "0%",
            "体验占比": f"{pain_counter.get('体验', 0)/n*100:.0f}%" if n else "0%",
            "服务占比": f"{pain_counter.get('服务', 0)/n*100:.0f}%" if n else "0%",
            "安全占比": f"{pain_counter.get('安全', 0)/n*100:.0f}%" if n else "0%",
            "高强度占比": f"{high_count/n*100:.0f}%" if n else "0%",
            "涉及画像数": len(personas),
            "涉及平台数": len(platforms),
            "竞品品牌TOP3": top3_comp,
            "汇总日期": str(date.today()),
        })

    return output


def write_csv(path: Path, fields: list[str], rows: list[dict]):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"  写入: {len(rows)} 行 → {path.name}")


def main():
    print("=" * 60)
    print(f"  P4 四维汇总编排器 ({date.today()})")
    print("=" * 60)

    raw_rows = load_extract()
    if not raw_rows:
        print("  [中止] 无源数据")
        return

    print(f"\n  源数据: {len(raw_rows)} 条 (dim_voc_negative_extract)")

    persona_rows = rollup_persona(raw_rows)
    write_csv(PERSONA_CSV, PERSONA_FIELDS, persona_rows)

    summary_rows = rollup_summary(raw_rows)
    write_csv(SUMMARY_CSV, SUMMARY_FIELDS, summary_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "=" * 60,
        f"  P4 汇总报告 ({date.today()})",
        "=" * 60,
        f"  源数据总行数: {len(raw_rows)}",
        f"  四维汇总行数: {len(persona_rows)} (国家×品线×画像×痛点)",
        f"  二维汇总行数: {len(summary_rows)} (国家×品线)",
        "",
    ]

    country_counter = Counter(r.get("国家", "") for r in raw_rows)
    report_lines.append("  国家覆盖:")
    for c, cnt in country_counter.most_common():
        report_lines.append(f"    {c}: {cnt} 条")

    line_counter = Counter(r.get("产品品线", "") for r in raw_rows)
    report_lines.append("\n  品线覆盖:")
    for l, cnt in line_counter.most_common():
        report_lines.append(f"    {l}: {cnt} 条")

    seg_counter = Counter(r.get("画像编码", "") for r in raw_rows)
    report_lines.append("\n  画像覆盖:")
    for s, cnt in sorted(seg_counter.items()):
        report_lines.append(f"    {s}: {cnt} 条")

    pain_counter = Counter(r.get("痛点大类(功能/价格/体验/服务/安全)", "") for r in raw_rows)
    report_lines.append("\n  痛点分布:")
    for p, cnt in pain_counter.most_common():
        report_lines.append(f"    {p}: {cnt} 条")

    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)
    print(report_text)

    report_path = OUTPUT_DIR / "p4_rollup_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    # 触发管道刷新
    import subprocess, sys
    export_script = PROJECT_ROOT / "tools" / "export_viz_json.py"
    validate_script = PROJECT_ROOT / "tools" / "validate_viz_dataset.py"

    print("\n  刷新数据管道...")
    r1 = subprocess.run([sys.executable, str(export_script)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if r1.returncode == 0:
        print("  export_viz_json.py [OK]")
    else:
        print(f"  export_viz_json.py [FAIL]\n{r1.stderr[:300]}")

    r2 = subprocess.run([sys.executable, str(validate_script)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if r2.returncode == 0:
        print("  validate_viz_dataset.py [OK]")
    else:
        print(f"  validate_viz_dataset.py [WARN]\n{r2.stderr[:300]}")


if __name__ == "__main__":
    main()
