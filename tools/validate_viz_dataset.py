# -*- coding: utf-8 -*-
"""
validate_viz_dataset.py — viz_dataset.json 数据质量校验。
可独立运行，也可被 export_viz_json.py 调用。

用法:
    python tools/validate_viz_dataset.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ))

DELIVERY_DIR = PROJ / "data" / "delivery"
OUTPUT = DELIVERY_DIR / "viz_dataset.json"

PRIORITY_VALID = {"P0", "P1", "P2", "P3"}


def run_checks(dataset: dict) -> tuple[int, int]:
    """运行全部校验规则，返回 (pass_count, fail_count)。"""
    passed = 0
    failed = 0

    def check(condition: bool, label: str):
        nonlocal passed, failed
        if condition:
            print(f"  OK   : {label}")
            passed += 1
        else:
            print(f"  FAIL : {label}")
            failed += 1

    def warn(condition: bool, label: str):
        nonlocal passed
        if condition:
            print(f"  OK   : {label}")
            passed += 1
        else:
            print(f"  WARN : {label}")
            passed += 1

    countries = dataset.get("countries", [])
    top20 = dataset.get("top20", [])
    meta = dataset.get("meta", {})
    trust_sources = dataset.get("trust_sources", [])
    keywords = dataset.get("keywords", [])

    print("\n=== 数据质量校验 ===\n")

    # ── 1. 关键数量检查 ──
    print("[数量检查]")
    check(len(countries) >= 41, f"countries.length >= 41 (actual: {len(countries)})")
    check(len(top20) == 20, f"top20.length == 20 (actual: {len(top20)})")

    is_top20_count = sum(1 for c in countries if c.get("is_top20"))
    check(is_top20_count == 20, f"countries.filter(is_top20).length == 20 (actual: {is_top20_count})")

    is_top10_count = sum(1 for c in countries if c.get("is_top10"))
    check(is_top10_count == 10, f"countries.filter(is_top10).length == 10 (actual: {is_top10_count})")

    check(
        meta.get("total_countries") == len(countries),
        f"meta.total_countries == countries.length ({meta.get('total_countries')} vs {len(countries)})",
    )

    # ── 2. 字段一致性检查 ──
    print("\n[字段一致性]")
    bad_insight_keys = [i for i, r in enumerate(top20) if "Insight" in r and "insight" not in r]
    check(
        len(bad_insight_keys) == 0,
        f"top20 entries use 'insight' not 'Insight' (bad rows: {bad_insight_keys})",
    )

    top20_with_insight = [r for r in top20 if r.get("insight")]
    warn(
        len(top20_with_insight) == len(top20),
        f"all top20 have non-null insight ({len(top20_with_insight)}/{len(top20)})",
    )

    top20_null_codes = [r.get("country") for r in top20 if not r.get("country_code")]
    check(
        len(top20_null_codes) == 0,
        f"all top20 have non-null country_code (null: {top20_null_codes})",
    )

    country_null_codes = [r.get("name_cn") for r in countries if not r.get("code")]
    check(
        len(country_null_codes) == 0,
        f"all countries have non-null code (null: {country_null_codes})",
    )

    # ── 3. 优先级合法值检查 ──
    print("\n[优先级合法值]")
    bad_trust_priorities = [
        (r.get("country"), r.get("priority"))
        for r in trust_sources
        if r.get("priority") and r["priority"] not in PRIORITY_VALID
    ]
    check(
        len(bad_trust_priorities) == 0,
        f"trust_sources.priority in {{P0..P3}} (invalid: {bad_trust_priorities[:5]})",
    )

    bad_kw_priorities = [
        (r.get("country"), r.get("crawl_priority"))
        for r in keywords
        if r.get("crawl_priority") and r["crawl_priority"] not in PRIORITY_VALID
    ]
    check(
        len(bad_kw_priorities) == 0,
        f"keywords.crawl_priority in {{P0..P3}} (invalid: {bad_kw_priorities[:5]})",
    )

    # ── 4. top20 与 countries 交叉一致性 ──
    print("\n[交叉一致性]")
    top20_codes = {r["country_code"] for r in top20 if r.get("country_code")}
    country_top20_codes = {c["code"] for c in countries if c.get("is_top20")}
    check(
        top20_codes == country_top20_codes,
        f"top20 codes == countries(is_top20) codes (diff: {top20_codes.symmetric_difference(country_top20_codes)})",
    )

    # ── 5. overview 数值类型检查 ──
    print("\n[overview 数值类型]")
    overview = dataset.get("overview", [])
    str_numbers = [
        r for r in overview
        if isinstance(r.get("value"), str) and _looks_numeric(r["value"])
    ]
    check(
        len(str_numbers) == 0,
        f"overview 无数值按字符串存储 (bad: {[(r['key'], r['value']) for r in str_numbers]})",
    )

    # ── 6. voc_negative 校验 ──
    print("\n[负面 VOC 数据校验]")
    voc_negative = dataset.get("voc_negative", [])
    warn(
        len(voc_negative) > 0,
        f"voc_negative has data (actual: {len(voc_negative)} rows)",
    )

    if voc_negative:
        missing_text = [
            i for i, r in enumerate(voc_negative) if not r.get("original_text")
        ]
        check(
            len(missing_text) == 0,
            f"voc_negative: all rows have original_text (missing: {len(missing_text)})",
        )

        missing_seg = [
            i for i, r in enumerate(voc_negative)
            if not r.get("segment_code") or not r.get("platform")
        ]
        check(
            len(missing_seg) == 0,
            f"voc_negative: 平台与画像不可脱钩 (missing segment_code or platform: {len(missing_seg)})",
        )

        dup_keys: list[str] = []
        seen_keys: set[str] = set()
        for r in voc_negative:
            url = r.get("source_url", "")
            text_prefix = (r.get("original_text") or "")[:50]
            key = f"{url}||{text_prefix}"
            if key in seen_keys:
                dup_keys.append(url[:60])
            else:
                seen_keys.add(key)
        check(
            len(dup_keys) == 0,
            f"voc_negative: no duplicate URL+text keys (dups: {len(dup_keys)})",
        )

        valid_pain = {"功能", "价格", "体验", "服务", "安全"}
        bad_pain = [
            r.get("pain_category") for r in voc_negative
            if r.get("pain_category") not in valid_pain
        ]
        check(
            len(bad_pain) == 0,
            f"voc_negative: pain_category in valid set (invalid: {bad_pain[:5]})",
        )

        valid_intensity = {"高", "中", "低"}
        bad_intensity = [
            r.get("intensity") for r in voc_negative
            if r.get("intensity") not in valid_intensity
        ]
        check(
            len(bad_intensity) == 0,
            f"voc_negative: intensity in {{高/中/低}} (invalid: {bad_intensity[:5]})",
        )

        valid_platform_types = {
            "social_media", "vertical_community", "vertical_official",
            "ecommerce", "search_engine", "competitor_dtc", "third_party_review",
        }
        bad_ptypes = [
            r.get("platform_type") for r in voc_negative
            if r.get("platform_type") and r["platform_type"] not in valid_platform_types
        ]
        check(
            len(bad_ptypes) == 0,
            f"voc_negative: platform_type in valid enum (invalid: {bad_ptypes[:5]})",
        )

        dtc_rows = [r for r in voc_negative if r.get("platform_type") == "competitor_dtc"]
        dtc_no_brand = [i for i, r in enumerate(dtc_rows) if not r.get("competitor_brand")]
        check(
            len(dtc_no_brand) == 0,
            f"voc_negative: DTC rows all have competitor_brand (missing: {len(dtc_no_brand)})",
        )

        zero_freq = [i for i, r in enumerate(voc_negative) if not r.get("frequency")]
        check(
            len(zero_freq) == 0,
            f"voc_negative: frequency non-null/non-zero (zeroes: {len(zero_freq)})",
        )

        import re
        garbage_pats = [
            re.compile(r"Cloudflare", re.I), re.compile(r"Target URL returned error", re.I),
            re.compile(r"^!\[Image", re.I), re.compile(r"CAPTCHA", re.I),
        ]
        garbage_rows = [
            i for i, r in enumerate(voc_negative)
            if any(p.search(r.get("original_text", "")) for p in garbage_pats)
        ]
        check(
            len(garbage_rows) == 0,
            f"voc_negative: no garbage text patterns (garbage: {len(garbage_rows)})",
        )

    # ── 7. voc_persona_summary 校验 ──
    print("\n[四维汇总校验]")
    voc_ps = dataset.get("voc_persona_summary", [])
    warn(
        len(voc_ps) > 0,
        f"voc_persona_summary has data (actual: {len(voc_ps)} rows)",
    )

    if voc_ps:
        missing_4d = [
            i for i, r in enumerate(voc_ps)
            if not all(r.get(k) for k in ("country", "product_line", "platform", "segment_code"))
        ]
        check(
            len(missing_4d) == 0,
            f"voc_persona_summary: all rows have 4D keys (missing: {len(missing_4d)})",
        )

    # ── 8. top20 负面字段校验 ──
    print("\n[top20 负面字段]")
    top20_with_neg = [r for r in top20 if r.get("top_negative_themes")]
    warn(
        len(top20_with_neg) > 0,
        f"top20 has negative themes (actual: {len(top20_with_neg)}/{len(top20)})",
    )

    # ── 汇总 ──
    print(f"\n=== 校验完成: {passed} passed, {failed} failed ===\n")
    return passed, failed


def _looks_numeric(s: str) -> bool:
    """判断一个字符串是否看起来像数值。"""
    try:
        float(s.replace(",", ""))
        return True
    except (ValueError, AttributeError):
        return False


def main():
    if not OUTPUT.exists():
        print(f"ERROR: {OUTPUT} not found. Run export_viz_json.py first.")
        sys.exit(1)
    with open(OUTPUT, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    passed, failed = run_checks(dataset)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
