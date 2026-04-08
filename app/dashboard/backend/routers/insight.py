# -*- coding: utf-8 -*-
"""
/api/v1/insight — 深度洞察数据 API。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()

PROCESSED_DIR = Path(__file__).resolve().parents[4] / "data" / "processed"

PRODUCT_LINE_FILE_MAP = {
    "breastpump": "insight_breastpump.json",
    "feedingappliance": "insight_feedingappliance.json",
}

PRODUCT_LINE_FILE_MAP_INTERNAL = {
    "breastpump": "insight_internal_breastpump.json",
    "feedingappliance": "insight_internal_feedingappliance.json",
}


@router.get("/internal/{product_line}")
def get_internal_insight(product_line: str) -> dict[str, Any]:
    """返回指定品线的内部 VOC 深度洞察 JSON。"""
    filename = PRODUCT_LINE_FILE_MAP_INTERNAL.get(product_line)
    if not filename:
        raise HTTPException(status_code=404, detail=f"Unknown product line: {product_line}")
    fpath = PROCESSED_DIR / filename
    if not fpath.exists():
        raise HTTPException(status_code=404, detail=f"Internal insight report not generated yet: {filename}")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/{product_line}")
def get_insight(product_line: str) -> dict[str, Any]:
    """返回指定品线的深度洞察 JSON。"""
    filename = PRODUCT_LINE_FILE_MAP.get(product_line)
    if not filename:
        raise HTTPException(status_code=404, detail=f"Unknown product line: {product_line}")
    fpath = PROCESSED_DIR / filename
    if not fpath.exists():
        raise HTTPException(status_code=404, detail=f"Insight report not generated yet: {filename}")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)
