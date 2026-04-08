"""
P0 采集脚本 4/4 — 批次编排器

功能：
  串联 P0 完整流程：
    1. 生成 Amazon URL 工作单
    2. 扫描 input/ 目录导入已采集的 JSON 批次
    3. 运行 SEG 画像匹配器
    4. 校验数据质量
    5. 触发数据管道刷新（export_viz_json + validate）

使用：
  python tools/collect/p0_batch_orchestrator.py
"""

from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = PROJECT_ROOT / "tools"
COLLECT_DIR = Path(__file__).parent
INPUT_DIR = COLLECT_DIR / "input"
OUTPUT_DIR = COLLECT_DIR / "output"
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"

VALID_PAIN = {"功能", "价格", "体验", "服务", "安全"}
VALID_INTENSITY = {"高", "中", "低"}
VALID_PRIORITY = {"P0", "P1", "P2", "P3"}


def step_banner(step: int, title: str):
    print(f"\n{'='*60}")
    print(f"  Step {step}: {title}")
    print(f"{'='*60}")


def step1_generate_urls():
    """Step 1: 生成 Amazon 采集 URL 工作单"""
    step_banner(1, "生成 Amazon 采集 URL 工作单")
    from p0_amazon_urls import main as gen_urls
    rows = gen_urls()
    return len(rows)


def step2_import_batches():
    """Step 2: 扫描并导入 input/ 下的 JSON 批次"""
    step_banner(2, "导入 JSON 批次文件")
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(INPUT_DIR.glob("*.json"))
    if not json_files:
        print("  [跳过] input/ 目录下无 JSON 文件")
        print(f"  提示: 将采集到的评论 JSON 放入 {INPUT_DIR}")
        return 0

    from p0_review_structurer import load_batch_json, append_to_csv

    total = 0
    for jf in json_files:
        rows = load_batch_json(jf)
        if rows:
            append_to_csv(rows)
            total += len(rows)
            processed = jf.with_suffix(".json.done")
            jf.rename(processed)
            print(f"  ✓ {jf.name} → {processed.name} ({len(rows)} 条)")

    print(f"  共导入 {total} 条")
    return total


def step3_seg_match():
    """Step 3: 运行 SEG 画像批量匹配"""
    step_banner(3, "SEG 画像批量匹配")
    from p0_seg_matcher import process_csv
    process_csv()


def step4_quality_check() -> dict:
    """Step 4: 数据质量校验"""
    step_banner(4, "数据质量校验")

    if not TARGET_CSV.exists():
        print("  [错误] 目标 CSV 不存在")
        return {"status": "FAIL"}

    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    issues = []
    country_counter = Counter()
    pain_counter = Counter()
    seg_counter = Counter()
    platform_counter = Counter()

    for i, row in enumerate(rows, 1):
        country = row.get("国家", "").strip()
        pain = row.get("痛点大类(功能/价格/体验/服务/安全)", "").strip()
        intensity = row.get("负面强度(高/中/低)", "").strip()
        seg = row.get("画像编码", "").strip()
        original = row.get("负面原文摘录(本地语言)", "").strip()
        theme = row.get("负面主题", "").strip()
        platform = row.get("平台", "").strip()

        if not country:
            issues.append(f"行{i}: 国家为空")
        else:
            country_counter[country] += 1

        if pain and pain not in VALID_PAIN:
            issues.append(f"行{i}: 无效痛点大类 '{pain}'")
        pain_counter[pain] += 1

        if intensity and intensity not in VALID_INTENSITY:
            issues.append(f"行{i}: 无效强度 '{intensity}'")

        if not seg:
            issues.append(f"行{i}: 画像编码为空")
        seg_counter[seg] += 1

        if not original:
            issues.append(f"行{i}: 原文为空")

        if not theme:
            issues.append(f"行{i}: 负面主题为空")

        platform_counter[platform] += 1

    print(f"\n  总行数: {len(rows)}")
    print(f"  质量问题: {len(issues)} 个")
    if issues[:10]:
        for iss in issues[:10]:
            print(f"    ⚠ {iss}")
        if len(issues) > 10:
            print(f"    ... 还有 {len(issues)-10} 个问题")

    print(f"\n  国家分布 (TOP10 覆盖率):")
    top10 = ["美国", "加拿大", "英国", "德国", "法国", "西班牙", "墨西哥", "阿联酋", "澳大利亚", "沙特阿拉伯"]
    covered = sum(1 for c in top10 if country_counter.get(c, 0) > 0)
    print(f"    已覆盖 {covered}/10 个国家")
    for c in top10:
        cnt = country_counter.get(c, 0)
        marker = "✓" if cnt > 0 else "✗"
        print(f"    {marker} {c}: {cnt} 条")

    print(f"\n  痛点分布:")
    for p in sorted(VALID_PAIN):
        print(f"    {p}: {pain_counter.get(p, 0)} 条")

    print(f"\n  画像分布:")
    for seg in sorted(seg_counter):
        print(f"    {seg}: {seg_counter[seg]} 条")

    print(f"\n  平台分布:")
    for plat, cnt in platform_counter.most_common(10):
        print(f"    {plat}: {cnt} 条")

    status = "PASS" if len(issues) == 0 else "WARN" if len(issues) < 5 else "FAIL"
    print(f"\n  质量状态: {status}")

    return {
        "status": status,
        "total": len(rows),
        "issues": len(issues),
        "coverage": covered,
    }


def step5_refresh_pipeline():
    """Step 5: 触发数据管道刷新"""
    step_banner(5, "刷新数据管道")

    export_script = TOOLS_DIR / "export_viz_json.py"
    validate_script = TOOLS_DIR / "validate_viz_dataset.py"

    print("  运行 export_viz_json.py ...")
    result = subprocess.run(
        [sys.executable, str(export_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  ✓ viz_dataset.json 已更新")
    else:
        print(f"  ✗ export 失败:\n{result.stderr[:500]}")
        return False

    print("  运行 validate_viz_dataset.py ...")
    result = subprocess.run(
        [sys.executable, str(validate_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    print(result.stdout[-500:] if result.stdout else "")
    if result.returncode == 0:
        print("  ✓ 数据校验通过")
    else:
        print(f"  ⚠ 校验有警告:\n{result.stderr[:500]}")

    return result.returncode == 0


def main():
    print("\n" + "=" * 60)
    print("  P0 采集批次编排器")
    print("  TOP10 × 吸奶器 × Amazon 1-2星评论")
    print("=" * 60)

    url_count = step1_generate_urls()
    import_count = step2_import_batches()
    step3_seg_match()
    quality = step4_quality_check()
    pipeline_ok = step5_refresh_pipeline()

    print("\n" + "=" * 60)
    print("  执行摘要")
    print("=" * 60)
    print(f"  URL 工作单: {url_count} 条")
    print(f"  新导入: {import_count} 条")
    print(f"  总数据: {quality.get('total', 0)} 条")
    print(f"  TOP10 覆盖: {quality.get('coverage', 0)}/10")
    print(f"  数据质量: {quality.get('status', 'N/A')}")
    print(f"  管道刷新: {'✓' if pipeline_ok else '✗'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
