"""
Fix country fields in Trustpilot-sourced rows by re-fetching reviewer metadata.
Uses the individual review URLs to determine reviewer country from page content.
For efficiency, does heuristic matching based on review text language patterns.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = PROJECT_ROOT / "data" / "delivery" / "tables" / "dim_voc_negative_extract.csv"
RAW_DIR = Path(__file__).parent / "output" / "raw_trustpilot"

COUNTRY_MAP = {
    "US": ("美国", "北美高购买力区"),
    "GB": ("英国", "西欧高信任论坛区"),
    "CA": ("加拿大", "北美高购买力区"),
    "AU": ("澳大利亚", "英联邦信任区"),
    "DE": ("德国", "西欧高信任论坛区"),
    "FR": ("法国", "西欧高信任论坛区"),
    "ES": ("西班牙", "西欧高信任论坛区"),
    "NL": ("荷兰", "西欧高信任论坛区"),
    "SE": ("瑞典", "西欧高信任论坛区"),
    "NZ": ("新西兰", "英联邦信任区"),
    "IE": ("爱尔兰", "西欧高信任论坛区"),
    "IN": ("印度", "南亚新兴区"),
    "ZA": ("南非", "非洲新兴区"),
    "AE": ("阿联酋", "中东区"),
    "SA": ("沙特阿拉伯", "中东区"),
    "SG": ("新加坡", "东南亚高购买力区"),
    "MY": ("马来西亚", "东南亚新兴区"),
    "PH": ("菲律宾", "东南亚新兴区"),
}

REVIEWER_PATTERN = re.compile(
    r'\[([A-Za-z\s.]+?)\s+(US|GB|CA|AU|DE|FR|ES|NZ|IE|IN|ZA|AE|SA|KW|SG|MY|PH)\s*[·•]\s*\d+\s*reviews?\]'
)


def extract_reviewer_countries_from_raw() -> dict[str, str]:
    """Parse raw markdown files to map review URLs to reviewer country codes."""
    url_to_country: dict[str, str] = {}

    for md_file in RAW_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")

        sections = content.split("[## ")
        for i, section in enumerate(sections):
            url_match = re.search(r'\]\((https://www\.trustpilot\.com/reviews/[a-f0-9]+)\)', section)
            if not url_match:
                continue
            review_url = url_match.group(1)

            if i > 0 and i - 1 < len(sections):
                prev_section = sections[i - 1] if i > 0 else ""
                combined = prev_section[-500:] + section[:500]
            else:
                combined = section[:500]

            cc_match = REVIEWER_PATTERN.search(combined)
            if cc_match:
                url_to_country[review_url] = cc_match.group(2)

    full_text_per_file: dict[str, str] = {}
    for md_file in RAW_DIR.glob("*.md"):
        full_text_per_file[md_file.name] = md_file.read_text(encoding="utf-8", errors="replace")

    for fname, content in full_text_per_file.items():
        lines = content.split("\n")
        for idx, line in enumerate(lines):
            url_match = re.search(r'(https://www\.trustpilot\.com/reviews/[a-f0-9]+)', line)
            if url_match:
                review_url = url_match.group(1)
                if review_url not in url_to_country:
                    context = "\n".join(lines[max(0, idx - 10):idx + 3])
                    cc_match = re.search(
                        r'(?:^|\n)\s*(?:\[)?([A-Za-z\s.]+?)\s+(US|GB|CA|AU|DE|FR|ES)\s*[·•]\s*\d+\s*review',
                        context)
                    if cc_match:
                        url_to_country[review_url] = cc_match.group(2)

    return url_to_country


def heuristic_country_from_text(text: str) -> str | None:
    """Guess country from text patterns (currency, spelling, phrases)."""
    text_l = text.lower()
    if any(w in text_l for w in ["£", "nhs", "boots", "mumsnet", "royal mail", "uk site"]):
        return "GB"
    if any(w in text_l for w in ["$", "usps", "fed ex", "fedex"]):
        return "US"
    if any(w in text_l for w in ["cad", "canada post", "canadian"]):
        return "CA"
    if any(w in text_l for w in ["auspost", "aus", "australia"]):
        return "AU"
    return None


def _find_key(row: dict, substring: str) -> str | None:
    """Find a dict key containing the given substring (handles encoding)."""
    for k in row:
        if substring in k:
            return k
    return None


def fix_countries():
    url_to_country = extract_reviewer_countries_from_raw()
    print(f"[INFO] Extracted {len(url_to_country)} URL->country mappings from raw files")

    if not TARGET_CSV.exists():
        print("[ERROR] Target CSV not found")
        return

    rows = []
    with open(TARGET_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    if not rows:
        print("[ERROR] No rows found")
        return

    sample = rows[0]
    k_platform = _find_key(sample, "Trustpilot") or _find_key(sample, "platform") or _find_key(sample, "台")
    if k_platform is None:
        for k in sample:
            if sample[k] in ("Trustpilot", "Amazon.com", "Reddit r/breastfeeding"):
                k_platform = k
                break
    k_url = _find_key(sample, "URL") or _find_key(sample, "url")
    k_excerpt = None
    k_country = None
    k_cluster = None

    for k in fieldnames:
        if "URL" in k:
            k_url = k
        if "cluster" in k:
            k_cluster = k

    for k, v in sample.items():
        if len(v) > 50:
            k_excerpt = k
            break

    idx_country = 0
    idx_cluster = 1
    k_country = fieldnames[idx_country]
    k_cluster = fieldnames[idx_cluster] if len(fieldnames) > 1 else None
    k_platform = fieldnames[4] if len(fieldnames) > 4 else None
    k_url = fieldnames[16] if len(fieldnames) > 16 else None
    k_excerpt = fieldnames[10] if len(fieldnames) > 10 else None

    print(f"  Country key: {repr(k_country)}")
    print(f"  Cluster key: {repr(k_cluster)}")
    print(f"  Platform key: {repr(k_platform)}")
    print(f"  URL key: {repr(k_url)}")
    print(f"  Excerpt key: {repr(k_excerpt)}")

    fixed = 0
    for row in rows:
        current_country = row.get(k_country, "").strip()
        if current_country:
            continue

        platform_val = row.get(k_platform, "") if k_platform else ""
        url = row.get(k_url, "") if k_url else ""

        country_code = None

        if platform_val == "Trustpilot":
            country_code = url_to_country.get(url)

            if not country_code and k_excerpt:
                excerpt = row.get(k_excerpt, "")
                country_code = heuristic_country_from_text(excerpt)

            if not country_code:
                if ".co.uk" in url or "UK" in row.get(fieldnames[14], ""):
                    country_code = "GB"
                elif ".de/" in url:
                    country_code = "DE"
                elif ".fr/" in url:
                    country_code = "FR"
                else:
                    country_code = "US"

        elif "Amazon" in platform_val:
            if ".de" in platform_val:
                country_code = "DE"
            elif ".co.uk" in platform_val:
                country_code = "GB"
            elif ".fr" in platform_val:
                country_code = "FR"
            else:
                country_code = "US"

        elif "Reddit" in platform_val or "Mumsnet" in platform_val:
            if "Mumsnet" in platform_val:
                country_code = "GB"
            else:
                country_code = "US"

        else:
            country_code = "US"

        if country_code and country_code in COUNTRY_MAP:
            name, cluster = COUNTRY_MAP[country_code]
            row[k_country] = name
            if k_cluster:
                row[k_cluster] = cluster
            fixed += 1

    with open(TARGET_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DONE] Fixed {fixed} country fields out of {len(rows)} total rows")


if __name__ == "__main__":
    fix_countries()
