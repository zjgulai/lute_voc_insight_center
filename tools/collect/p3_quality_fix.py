"""
P3 Quality Pass: clean up dim_voc_negative_extract.csv
- Remove placeholder/example rows
- Normalize brand names
- Generate summary stats
"""
import csv
from collections import Counter
from pathlib import Path

CSV = Path(r'd:\专题2：VOC分析\voc-data-product\data\delivery\tables\dim_voc_negative_extract.csv')

with open(CSV, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fns = reader.fieldnames
    rows = list(reader)

print(f"[P3] Start: {len(rows)} rows")

url_key = fns[16]
brand_key = fns[14]

before = len(rows)
rows = [r for r in rows if "example" not in r[url_key]]
removed = before - len(rows)
print(f"[P3] Removed {removed} placeholder rows")

brand_norm = {
    "S2;Spectra": "Spectra",
    "Medela;Spectra": "Medela",
}
fixed_brands = 0
for row in rows:
    brand = row[brand_key]
    if brand in brand_norm:
        row[brand_key] = brand_norm[brand]
        fixed_brands += 1
print(f"[P3] Normalized {fixed_brands} brand names")

with open(CSV, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fns)
    writer.writeheader()
    writer.writerows(rows)

print(f"[P3] Final: {len(rows)} rows")
print()

print("=== P4 Summary Statistics ===")
print(f"Total records: {len(rows)}")
print()

print("By Brand:")
c = Counter(row[brand_key] for row in rows)
for v, cnt in c.most_common(20):
    pct = cnt / len(rows) * 100
    print(f"  {v:25s}: {cnt:3d} ({pct:4.1f}%)")

print()
print("By Product Line:")
c = Counter(row[fns[2]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    print(f"  {v}: {cnt} ({pct:.1f}%)")

print()
print("By Pain Category:")
c = Counter(row[fns[8]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    print(f"  {v}: {cnt} ({pct:.1f}%)")

print()
print("By Intensity:")
c = Counter(row[fns[13]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    print(f"  {v}: {cnt} ({pct:.1f}%)")

print()
print("By Platform:")
c = Counter(row[fns[4]] for row in rows)
for v, cnt in c.most_common():
    pct = cnt / len(rows) * 100
    print(f"  {v}: {cnt} ({pct:.1f}%)")

print()
print("Top 15 Negative Themes:")
c = Counter(row[fns[9]] for row in rows)
for v, cnt in c.most_common(15):
    pct = cnt / len(rows) * 100
    print(f"  {v}: {cnt} ({pct:.1f}%)")
