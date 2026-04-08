# -*- coding: utf-8 -*-
"""
/api/v1/opportunity — 机会点挖掘看板数据 API。
"""
from __future__ import annotations

from fastapi import APIRouter

from services.dataset_service import get_opportunity

router = APIRouter()


@router.get("/data")
def opportunity_data() -> dict:
    """返回机会点挖掘看板完整数据集。"""
    return get_opportunity()
