# -*- coding: utf-8 -*-
"""
ETL 编排服务 — 封装 CSV 状态检查、导出脚本调用、校验触发。
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJ_ROOT = Path(__file__).resolve().parents[4]
TABLES_DIR = PROJ_ROOT / "data" / "delivery" / "tables"
DELIVERY_DIR = PROJ_ROOT / "data" / "delivery"
TOOLS_DIR = PROJ_ROOT / "tools"

DASHBOARD_SOURCE_MAP = {
    "country_insight": [
        "dim_project_meta.csv",
        "dim_country_product_persona.csv",
        "dim_top20_country_insight.csv",
        "dim_cluster_strategy.csv",
        "dim_country_price_sensitivity.csv",
        "dim_country_segment_matrix.csv",
        "cfg_top10_platform_entry.csv",
        "cfg_top10_country_line.csv",
    ],
    "opportunity": [
        "voc_summary_flat.csv",
        "voc_summary_persona_flat.csv",
        "dim_voc_negative_extract.csv",
        "dim_info_source_quality.csv",
        "cfg_p1_search_playbook.csv",
        "cfg_top10_platform_entry.csv",
    ],
}


def get_table_status() -> list[dict[str, Any]]:
    """Return file status for all source CSVs."""
    all_files = set()
    for files in DASHBOARD_SOURCE_MAP.values():
        all_files.update(files)

    result = []
    for fname in sorted(all_files):
        fpath = TABLES_DIR / fname
        dashboards = [k for k, v in DASHBOARD_SOURCE_MAP.items() if fname in v]
        if fpath.exists():
            stat = fpath.stat()
            line_count = sum(1 for _ in open(fpath, encoding="utf-8-sig")) - 1
            result.append({
                "filename": fname,
                "exists": True,
                "rows": max(0, line_count),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "dashboards": dashboards,
            })
        else:
            result.append({
                "filename": fname,
                "exists": False,
                "rows": 0,
                "size_bytes": 0,
                "modified_at": None,
                "dashboards": dashboards,
            })
    return result


def get_json_status() -> list[dict[str, Any]]:
    """Return status of output JSON files."""
    json_files = [
        "viz_country_insight.json",
        "viz_opportunity.json",
        "viz_opportunity_internal.json",
        "viz_dataset.json",
    ]
    result = []
    for fname in json_files:
        fpath = DELIVERY_DIR / fname
        if fpath.exists():
            stat = fpath.stat()
            result.append({
                "filename": fname,
                "exists": True,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        else:
            result.append({
                "filename": fname,
                "exists": False,
                "size_bytes": 0,
                "modified_at": None,
            })
    return result


def run_export() -> dict[str, Any]:
    """Run the export_viz_json.py script."""
    try:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "export_viz_json.py")],
            capture_output=True, text=True, timeout=60,
            cwd=str(PROJ_ROOT),
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": "Timeout after 60s"}
    except Exception as e:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": str(e)}


def run_sentiment_batch_ingest() -> dict[str, Any]:
    """Run the sentiment batch ingest script."""
    script = TOOLS_DIR / "collect" / "ingest_sentiment_batch.py"
    if not script.exists():
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": "Script not found"}
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=180,
            cwd=str(PROJ_ROOT),
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": "Timeout after 180s"}
    except Exception as e:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": str(e)}


def run_competitor_ingest() -> dict[str, Any]:
    """Run the competitor ZIP ingest script."""
    script = TOOLS_DIR / "collect" / "ingest_competitor_zip.py"
    if not script.exists():
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": "Script not found"}
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(PROJ_ROOT),
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": "Timeout after 120s"}
    except Exception as e:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": str(e)}


def run_validate() -> dict[str, Any]:
    """Run the validation script."""
    script = TOOLS_DIR / "validate_viz_dataset.py"
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"import json; from pathlib import Path; "
             f"from tools.validate_viz_dataset import run_checks; "
             f"ds = json.loads(Path(r'{DELIVERY_DIR / 'viz_dataset.json'}').read_text('utf-8')); "
             f"p, f = run_checks(ds); print(f'passed={{p}} failed={{f}}')"],
            capture_output=True, text=True, timeout=30,
            cwd=str(PROJ_ROOT),
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except Exception as e:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": str(e)}
