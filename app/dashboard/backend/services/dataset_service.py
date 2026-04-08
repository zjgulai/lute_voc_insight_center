# -*- coding: utf-8 -*-
"""
双看板数据集管理服务 — 读取并缓存三份 JSON（国家洞察、机会点、merged）。
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "delivery"

COUNTRY_INSIGHT_FILE = _DATA_DIR / "viz_country_insight.json"
OPPORTUNITY_FILE = _DATA_DIR / "viz_opportunity.json"
MERGED_FILE = _DATA_DIR / "viz_dataset.json"


@lru_cache(maxsize=1)
def _load_country_insight() -> dict[str, Any]:
    with open(COUNTRY_INSIGHT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_opportunity() -> dict[str, Any]:
    with open(OPPORTUNITY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_merged() -> dict[str, Any]:
    with open(MERGED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_country_insight() -> dict[str, Any]:
    return _load_country_insight()


def get_opportunity() -> dict[str, Any]:
    return _load_opportunity()


def get_merged() -> dict[str, Any]:
    return _load_merged()


def reload_all() -> None:
    """Clear all dataset caches."""
    _load_country_insight.cache_clear()
    _load_opportunity.cache_clear()
    _load_merged.cache_clear()
