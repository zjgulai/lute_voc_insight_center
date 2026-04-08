import csv
from collections import Counter

CSV = r'd:\专题2：VOC分析\voc-data-product\data\delivery\tables\dim_voc_negative_extract.csv'
rows = list(csv.DictReader(open(CSV, 'r', encoding='utf-8')))
print(f"Total rows: {len(rows)}")

brands = Counter(r.get("\u7ade\u54c1\u5173\u8054\u54c1\u724c","") for r in rows)
print("\nBy brand:")
for b, c in brands.most_common():
    print(f"  {b}: {c}")

countries = Counter(r.get("\u56fd\u5bb6","") for r in rows)
print("\nBy country:")
for co, c in countries.most_common():
    print(f"  {co}: {c}")

pains = Counter(r.get("\u75db\u70b9\u5927\u7c7b(\u529f\u80fd/\u4ef7\u683c/\u4f53\u9a8c/\u670d\u52a1/\u5b89\u5168)","") for r in rows)
print("\nBy pain category:")
for p, c in pains.most_common():
    print(f"  {p}: {c}")

platforms = Counter(r.get("\u5e73\u53f0","") for r in rows)
print("\nBy platform:")
for p, c in platforms.most_common():
    print(f"  {p}: {c}")

print("\nSample new rows (last 3):")
for r in rows[-3:]:
    brand = r.get("\u7ade\u54c1\u5173\u8054\u54c1\u724c","")
    co = r.get("\u56fd\u5bb6","")
    pain = r.get("\u75db\u70b9\u5927\u7c7b(\u529f\u80fd/\u4ef7\u683c/\u4f53\u9a8c/\u670d\u52a1/\u5b89\u5168)","")
    excerpt = r.get("\u8d1f\u9762\u539f\u6587\u6458\u5f55(\u672c\u5730\u8bed\u8a00)","")[:100]
    print(f"  [{brand}][{co}][{pain}] {excerpt}")
