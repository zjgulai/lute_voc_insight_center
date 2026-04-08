# -*- coding: utf-8 -*-
"""
/api/v1/countries — 国家维度 API。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.country_service import (
    get_all_countries,
    get_country_by_code,
    get_country_detail,
)

router = APIRouter()


@router.get("/")
def list_countries(
    top20: bool | None = None,
    top10: bool | None = None,
) -> list[dict]:
    countries = get_all_countries()
    if top20 is not None:
        countries = [c for c in countries if c.get("is_top20") == top20]
    if top10 is not None:
        countries = [c for c in countries if c.get("is_top10") == top10]
    return countries


@router.get("/{code}")
def get_country(code: str) -> dict:
    detail = get_country_detail(code)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Country '{code}' not found")
    return detail
