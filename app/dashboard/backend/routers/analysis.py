# -*- coding: utf-8 -*-
"""
/api/v1/analysis — 国家洞察看板数据 API。
"""
from __future__ import annotations

from fastapi import APIRouter

from services.dataset_service import get_country_insight

router = APIRouter()


@router.get("/data")
def analysis_data() -> dict:
    """返回国家洞察看板完整数据集。"""
    return get_country_insight()
