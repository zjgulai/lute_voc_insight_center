import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else r"output\raw_dtc\momcozy_okendo_m5_low.json"
with open(path, "r", encoding="utf-8") as f:
    d = json.load(f)

print(f"Type: {type(d).__name__}")
if isinstance(d, dict):
    print(f"Keys: {list(d.keys())[:10]}")
    reviews = d.get("reviews", d.get("data", []))
    if isinstance(reviews, list):
        print(f"Reviews count: {len(reviews)}")
        for r in reviews[:5]:
            print("---")
            rating = r.get("rating", "?")
            body = r.get("body", r.get("reviewBody", r.get("text", "")))
            title = r.get("title", r.get("heading", ""))
            print(f"  Rating: {rating}")
            print(f"  Title: {title[:80]}")
            print(f"  Body: {str(body)[:200]}")
    else:
        print(f"Reviews type: {type(reviews)}")
        print(str(reviews)[:300])
else:
    print(str(d)[:500])
