# -*- coding: utf-8 -*-
"""
国家数据服务层 — 从 viz_dataset.json 读取并提供国家相关数据。
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

VIZ_FILE = Path(__file__).resolve().parents[4] / "data" / "delivery" / "viz_dataset.json"


@lru_cache(maxsize=1)
def _load_dataset() -> dict[str, Any]:
    with open(VIZ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def reload_dataset() -> None:
    _load_dataset.cache_clear()


def get_dataset() -> dict[str, Any]:
    return _load_dataset()


def get_all_countries() -> list[dict]:
    return get_dataset().get("countries", [])


def get_country_by_code(code: str) -> dict | None:
    code_upper = code.upper()
    for c in get_all_countries():
        if c.get("code") == code_upper:
            return c
    return None


def get_country_detail(code: str) -> dict | None:
    """聚合单个国家的所有维度数据。"""
    code_upper = code.upper()
    country = get_country_by_code(code_upper)
    if not country:
        return None

    ds = get_dataset()
    return {
        "country": country,
        "personas": [
            p for p in ds.get("personas", []) if p.get("country_code") == code_upper
        ],
        "purchasing_power": [
            pp for pp in ds.get("purchasing_power", []) if pp.get("country_code") == code_upper
        ],
        "trust_sources": [
            ts for ts in ds.get("trust_sources", []) if ts.get("country_code") == code_upper
        ],
        "platforms": [
            pl for pl in ds.get("platforms", []) if pl.get("country_code") == code_upper
        ],
        "keywords": [
            kw for kw in ds.get("keywords", []) if kw.get("country_code") == code_upper
        ],
        "voc_summary": [
            vs for vs in ds.get("voc_summary", []) if vs.get("country_code") == code_upper
        ],
        "brand_voc_summary": [
            vs for vs in ds.get("brand_voc_summary", []) if vs.get("country_code") == code_upper
        ],
    }


def get_overview() -> list[dict]:
    return get_dataset().get("overview", [])


def get_meta() -> dict:
    return get_dataset().get("meta", {})
