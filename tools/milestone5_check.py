# -*- coding: utf-8 -*-
"""里程碑5：全链路综合验证脚本"""
import json
import sys
import os
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), "w", encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
results = []

def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    results.append((name, status, detail))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("里程碑5 — 全链路验证")
print("=" * 60)

# 1. 数据真源
print("\n─── 1. 数据真源 ───")
viz_path = ROOT / "data" / "delivery" / "viz_dataset.json"
check("viz_dataset.json 存在", viz_path.exists())
if viz_path.exists():
    data = json.loads(viz_path.read_text(encoding="utf-8"))
    expected_keys = {"meta", "overview", "countries", "personas", "top20", "clusters",
                     "purchasing_power", "trust_sources", "platforms", "keywords", "voc_summary"}
    actual_keys = set(data.keys())
    check("11 个顶层 section", expected_keys.issubset(actual_keys), f"found {len(actual_keys)}")
    check("countries >= 40", len(data.get("countries", [])) >= 40, str(len(data.get("countries", []))))
    check("personas > 0", len(data.get("personas", [])) > 0, str(len(data.get("personas", []))))

# 2. 路径配置
print("\n─── 2. 路径配置 ───")
check("app_paths.py 存在", (ROOT / "config" / "app_paths.py").exists())
check("archive_paths.py 存在", (ROOT / "config" / "archive_paths.py").exists())

# 3. 后端
print("\n─── 3. 后端 ───")
backend = ROOT / "app" / "dashboard" / "backend"
check("main.py 存在", (backend / "main.py").exists())
check("routers/countries.py 存在", (backend / "routers" / "countries.py").exists())
check("routers/research.py 存在", (backend / "routers" / "research.py").exists())
check("services/country_service.py 存在", (backend / "services" / "country_service.py").exists())

# 4. 前端
print("\n─── 4. 前端 ───")
frontend = ROOT / "app" / "dashboard" / "frontend"
check("layout.tsx 存在", (frontend / "app" / "layout.tsx").exists())
check("page.tsx (概览) 存在", (frontend / "app" / "page.tsx").exists())
check("viz/page.tsx 存在", (frontend / "app" / "viz" / "page.tsx").exists())
check("countries/page.tsx 存在", (frontend / "app" / "countries" / "page.tsx").exists())
check("countries/[code]/page.tsx 存在", (frontend / "app" / "countries" / "[code]" / "page.tsx").exists())
check("admin/page.tsx 存在", (frontend / "app" / "admin" / "page.tsx").exists())
check("lib/api.ts 存在", (frontend / "lib" / "api.ts").exists())

# 5. viz-static
print("\n─── 5. viz-static 独立交付站 ───")
viz_static = ROOT / "viz-static"
check("viz-static/index.html 存在", (viz_static / "index.html").exists())
check("viz-static/src/App.tsx 存在", (viz_static / "src" / "App.tsx").exists())
check("viz-static/dist/ 构建产物存在", (viz_static / "dist" / "index.html").exists())
sections_dir = viz_static / "src" / "sections"
section_files = list(sections_dir.glob("*.tsx")) if sections_dir.exists() else []
check("8 个 section 组件", len(section_files) == 8, f"found {len(section_files)}")

# 6. 归档完整性
print("\n─── 6. 归档完整性 ───")
archive = ROOT / "archive"
check("archive/legacy/ 存在", (archive / "legacy").exists())
check("archive/legacy-scripts/ 存在", (archive / "legacy-scripts").exists())
check("archive/scope/ 存在", (archive / "scope").exists())
check("archive/backend_v1/ 存在", (archive / "backend_v1").exists())
check("archive/frontend_v1/ 存在", (archive / "frontend_v1").exists())

# 7. 文档
print("\n─── 7. 文档 ───")
check("README.md 存在", (ROOT / "README.md").exists())
check("docs/00_项目导航.md 存在", (ROOT / "docs" / "00_项目导航.md").exists())
check("docs/03_数据交付/visualization_field_mapping.md 存在",
      (ROOT / "docs" / "03_数据交付" / "visualization_field_mapping.md").exists())

# 8. 工具
print("\n─── 8. 工具 ───")
check("tools/export_viz_json.py 存在", (ROOT / "tools" / "export_viz_json.py").exists())
check("tools/validate_viz_dataset.py 存在", (ROOT / "tools" / "validate_viz_dataset.py").exists())

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
total = len(results)
print(f"总计: {passed}/{total} PASS, {failed} FAIL")
if failed == 0:
    print("里程碑5 — 全链路验证 PASSED")
else:
    print("里程碑5 — 全链路验证 FAILED")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  FAIL: {name} {detail}")
print("=" * 60)
