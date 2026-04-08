import csv
from collections import Counter

CSV = r'd:\专题2：VOC分析\voc-data-product\data\delivery\tables\dim_voc_negative_extract.csv'
with open(CSV, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fns = reader.fieldnames
    rows = list(reader)

print(f"=== VOC Negative Data Quality Report ===")
print(f"Total rows: {len(rows)}")
print(f"Total fields: {len(fns)}")
print()

labels = [
    'Country', 'Region Cluster', 'Product Line', 'Platform Type', 'Platform',
    'Persona Code', 'Persona Name', 'Lifecycle',
    'Pain Category', 'Negative Theme', 'Excerpt (Local)', 'Excerpt (CN)',
    'Frequency Est.', 'Intensity', 'Competitor Brand', 'Ops Suggestion',
    'Source URL', 'Collection Date', 'Batch Code', 'Priority',
]

for i, label in enumerate(labels):
    if i >= len(fns):
        break
    key = fns[i]
    vals = [row[key] for row in rows]
    non_empty = sum(1 for v in vals if v.strip())
    fill_pct = non_empty / len(rows) * 100
    unique = len(set(v for v in vals if v.strip()))
    sample = vals[0][:30] if vals and vals[0] else ""
    print(f"  {label:25s} | fill: {fill_pct:5.1f}% | uniq: {unique:3d}")

print()
print("--- By Brand ---")
brand_key = fns[14]
c = Counter(row[brand_key] for row in rows)
for v, cnt in c.most_common(20):
    print(f"  {v:25s}: {cnt}")

print()
print("--- By Country ---")
country_key = fns[0]
c = Counter(row[country_key] for row in rows)
for v, cnt in c.most_common(10):
    print(f"  {v}: {cnt}")

print()
print("--- By Product Line ---")
line_key = fns[2]
c = Counter(row[line_key] for row in rows)
for v, cnt in c.most_common(10):
    print(f"  {v}: {cnt}")

print()
print("--- By Platform ---")
plat_key = fns[4]
c = Counter(row[plat_key] for row in rows)
for v, cnt in c.most_common(10):
    print(f"  {v}: {cnt}")

print()
print("--- By Pain Category ---")
pain_key = fns[8]
c = Counter(row[pain_key] for row in rows)
for v, cnt in c.most_common(10):
    print(f"  {v}: {cnt}")

print()
print("--- By Intensity ---")
int_key = fns[13]
c = Counter(row[int_key] for row in rows)
for v, cnt in c.most_common(5):
    print(f"  {v}: {cnt}")

print()
print("--- By Batch ---")
batch_key = fns[18]
c = Counter(row[batch_key] for row in rows)
for v, cnt in c.most_common(20):
    print(f"  {v}: {cnt}")
