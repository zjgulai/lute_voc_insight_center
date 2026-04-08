# -*- coding: utf-8 -*-
"""里程碑3验证脚本：后端 API 端点测试。"""
import json
import sys
import io
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "http://127.0.0.1:8000"
tests = [
    ("GET /health", f"{BASE}/health"),
    ("GET /api/v1/countries/", f"{BASE}/api/v1/countries/"),
    ("GET /api/v1/countries/US", f"{BASE}/api/v1/countries/US"),
    ("GET /api/v1/research/meta", f"{BASE}/api/v1/research/meta"),
    ("GET /api/v1/research/overview", f"{BASE}/api/v1/research/overview"),
    ("GET /api/v1/research/viz-data", f"{BASE}/api/v1/research/viz-data"),
    ("GET /api/v1/research/clusters", f"{BASE}/api/v1/research/clusters"),
    ("GET /api/v1/research/top20", f"{BASE}/api/v1/research/top20"),
]

print("========== 里程碑3：后端API端点验证 ==========\n")
all_pass = True
for name, url in tests:
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                summary = f"{len(data)} items"
            elif isinstance(data, dict):
                keys = list(data.keys())[:5]
                summary = f"keys: {keys}"
            else:
                summary = str(data)[:60]
            print(f"  [{name}] -> 200 OK | {summary}")
    except Exception as e:
        print(f"  [{name}] -> FAIL: {e}")
        all_pass = False

result = "PASS" if all_pass else "FAIL"
print(f"\n========== OVERALL: {result} ==========")
sys.exit(0 if all_pass else 1)
