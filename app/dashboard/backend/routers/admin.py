# -*- coding: utf-8 -*-
"""
/api/v1/admin — 运营后台 API（数据源状态、导出、校验、竞品导入、预览）。
"""
from __future__ import annotations

import csv
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from services.dataset_service import reload_all
from services.country_service import reload_dataset
from services.etl_service import (
    get_table_status,
    get_json_status,
    run_export,
    run_competitor_ingest,
    run_sentiment_batch_ingest,
    run_validate,
    TABLES_DIR,
)

router = APIRouter()


@router.get("/status")
def admin_status() -> dict[str, Any]:
    """返回数据源文件状态和 JSON 产物状态。"""
    return {
        "tables": get_table_status(),
        "json_outputs": get_json_status(),
    }


@router.post("/export")
def admin_export() -> dict[str, Any]:
    """执行 export_viz_json.py 重新生成三份 JSON。"""
    result = run_export()
    if result["success"]:
        reload_dataset()
        reload_all()
    return result


@router.post("/ingest-competitor-zip")
def admin_ingest_competitor() -> dict[str, Any]:
    """执行竞品 ZIP 解压、负面筛选、入表。"""
    return run_competitor_ingest()


@router.post("/ingest-sentiment-batch")
def admin_ingest_sentiment() -> dict[str, Any]:
    """执行情感泛化词批次导入（从 02_sentiment_batch/ 目录）。"""
    return run_sentiment_batch_ingest()


@router.post("/validate")
def admin_validate() -> dict[str, Any]:
    """运行数据校验脚本。"""
    return run_validate()


@router.post("/reload")
def admin_reload() -> dict[str, str]:
    """统一 reload 所有数据集缓存。"""
    reload_dataset()
    reload_all()
    return {"status": "reloaded"}


@router.get("/download-csv")
def download_csv(table: str = Query(..., description="CSV 文件名")) -> FileResponse:
    """直接下载指定 CSV 文件。"""
    fpath = TABLES_DIR / table
    if not fpath.exists():
        raise HTTPException(status_code=404, detail=f"{table} not found")
    return FileResponse(
        path=str(fpath),
        filename=table,
        media_type="text/csv; charset=utf-8-sig",
    )


@router.get("/preview")
def admin_preview(
    table: str = Query(..., description="CSV 文件名（不含路径）"),
    country: str | None = Query(None),
    product_line: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """预览 CSV 数据（分页、可按国家/品线筛选）。"""
    fpath = TABLES_DIR / table
    if not fpath.exists():
        return {"error": f"Table {table} not found", "rows": [], "total": 0}

    rows_out: list[dict] = []
    total = 0
    with open(fpath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if country and r.get("国家", "") != country:
                continue
            if product_line and r.get("产品品线", "") != product_line:
                continue
            total += 1
            start = (page - 1) * page_size
            end = start + page_size
            if start < total <= end:
                rows_out.append(r)

    return {
        "table": table,
        "total": total,
        "page": page,
        "page_size": page_size,
        "rows": rows_out,
    }
