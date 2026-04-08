# -*- coding: utf-8 -*-
"""
/api/v1/research — 研究维度 API（含可视化数据端点）。
"""
from __future__ import annotations

from fastapi import APIRouter

from services.country_service import get_dataset, get_meta, get_overview, reload_dataset
from services.dataset_service import reload_all as reload_all_datasets

router = APIRouter()


@router.get("/viz-data")
def viz_data() -> dict:
    """返回完整 viz_dataset.json 内容供前端渲染。"""
    return get_dataset()


@router.get("/overview")
def overview() -> list[dict]:
    return get_overview()


@router.get("/meta")
def meta() -> dict:
    return get_meta()


@router.get("/clusters")
def clusters() -> list[dict]:
    return get_dataset().get("clusters", [])


@router.get("/top20")
def top20() -> list[dict]:
    return get_dataset().get("top20", [])


@router.get("/personas")
def personas(country_code: str | None = None) -> list[dict]:
    data = get_dataset().get("personas", [])
    if country_code:
        data = [p for p in data if p.get("country_code") == country_code.upper()]
    return data


@router.get("/purchasing-power")
def purchasing_power(country_code: str | None = None) -> list[dict]:
    data = get_dataset().get("purchasing_power", [])
    if country_code:
        data = [p for p in data if p.get("country_code") == country_code.upper()]
    return data


@router.get("/trust-sources")
def trust_sources(country_code: str | None = None) -> list[dict]:
    data = get_dataset().get("trust_sources", [])
    if country_code:
        data = [t for t in data if t.get("country_code") == country_code.upper()]
    return data


@router.post("/reload")
def reload() -> dict:
    """强制重新加载所有数据集缓存。"""
    reload_dataset()
    reload_all_datasets()
    return {"status": "reloaded"}
