"""Service: research collection gap analysis & input-version management."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from services.research_reader import ResearchReader
from utils.country_names import ISO_TO_CN

_PRODUCT_LINES = ["吸奶器", "喂养电器", "家居出行", "洗护", "棉品", "辅食", "综合"]

_KEY_TABLES: list[dict] = [
    {"table": "dim_country_product_persona.csv", "field": "身份画像", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "dim_country_product_persona.csv", "field": "媒体偏好", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "dim_country_product_persona.csv", "field": "购买习惯", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "dim_country_product_persona.csv", "field": "品牌偏好", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "dim_country_product_persona.csv", "field": "营销偏好", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "dim_country_product_persona.csv", "field": "社媒传播类平台", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "dim_country_product_persona.csv", "field": "垂类社区平台", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "dim_country_product_persona.csv", "field": "垂类官方媒体平台", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "cfg_top10_platform_entry.csv", "field": "入口/版块", "col_country": "国家", "col_pl": None},
    {"table": "cfg_top10_platform_entry.csv", "field": "关键词包", "col_country": "国家", "col_pl": None},
    {"table": "cfg_top10_platform_entry.csv", "field": "采样建议", "col_country": "国家", "col_pl": None},
    {"table": "cfg_p1_search_playbook.csv", "field": "站内搜索语句", "col_country": "国家", "col_pl": "产品品线"},
    {"table": "cfg_p1_search_playbook.csv", "field": "社区布尔组合", "col_country": "国家", "col_pl": "产品品线"},
]


class ResearchGapService:
    def __init__(self, product_root: Path) -> None:
        self._root = product_root
        self._reader = ResearchReader(product_root)
        self._versions_path = product_root / "data" / "inputs" / "input_versions.json"
        self._all_countries_cn: list[str] = sorted(set(ISO_TO_CN.values()))

    def _load_table_rows(self, csv_name: str) -> list[dict[str, str]]:
        return self._reader._read_table(csv_name)

    def _countries_in_table(self, csv_name: str, col_country: str) -> set[str]:
        rows = self._load_table_rows(csv_name)
        return {r.get(col_country, "").strip() for r in rows if r.get(col_country, "").strip()}

    def collection_gaps(
        self,
        country: str | None = None,
        product_line: str | None = None,
        platform_type: str | None = None,
        priority: str | None = None,
    ) -> dict:
        """Compute per-country×product-line gap rows."""
        table_cache: dict[str, list[dict[str, str]]] = {}
        for spec in _KEY_TABLES:
            tname = spec["table"]
            if tname not in table_cache:
                table_cache[tname] = self._load_table_rows(tname)

        def _has_value(rows: list[dict], country_cn: str, pl: str | None, field: str, col_c: str, col_p: str | None) -> bool:
            for r in rows:
                if r.get(col_c, "").strip() != country_cn:
                    continue
                if col_p and pl and r.get(col_p, "").strip() != pl:
                    continue
                val = r.get(field, "").strip()
                if val:
                    return True
            return False

        countries_to_check = self._all_countries_cn
        if country:
            countries_to_check = [c for c in countries_to_check if country.lower() in c.lower()]

        product_lines = _PRODUCT_LINES
        if product_line:
            product_lines = [pl for pl in product_lines if pl == product_line]

        gap_rows: list[dict] = []
        total_fields = len(_KEY_TABLES)

        for c in countries_to_check:
            for pl in product_lines:
                missing: list[str] = []
                for spec in _KEY_TABLES:
                    tname = spec["table"]
                    field = spec["field"]
                    col_c = spec["col_country"]
                    col_p = spec["col_pl"]
                    if not _has_value(table_cache[tname], c, pl if col_p else None, field, col_c, col_p):
                        missing.append(field)

                if not missing:
                    continue

                prio = self._compute_priority(c, pl)
                if priority and prio != priority:
                    continue

                gap_rows.append({
                    "country": c,
                    "product_line": pl,
                    "missing_fields": missing,
                    "missing_count": len(missing),
                    "completion_rate": round(1 - len(missing) / total_fields, 3),
                    "priority": prio,
                    "status": "draft",
                    "last_updated": "",
                })

        gap_rows.sort(key=lambda r: (-{"P0": 3, "P1": 2, "P2": 1}.get(r["priority"], 0), -r["missing_count"]))

        countries_involved = {r["country"] for r in gap_rows}
        total_gaps = sum(r["missing_count"] for r in gap_rows)
        avg_comp = (
            sum(r["completion_rate"] for r in gap_rows) / len(gap_rows) if gap_rows else 1.0
        )

        return {
            "rows": gap_rows,
            "count": len(gap_rows),
            "summary": {
                "total_countries": len(countries_involved),
                "total_gaps": total_gaps,
                "avg_completion": round(avg_comp, 3),
            },
        }

    def _compute_priority(self, country_cn: str, product_line: str) -> str:
        top10 = self._load_table_rows("cfg_top10_country_line.csv")
        top10_countries = {r.get("国家", "").strip() for r in top10}
        top20_countries = {r.get("国家", "").strip() for r in self._load_table_rows("dim_top20_country_insight.csv")}

        if country_cn in top10_countries:
            return "P0"
        if country_cn in top20_countries:
            return "P1"
        return "P2"

    def _load_versions(self) -> list[dict]:
        if not self._versions_path.exists():
            return []
        try:
            data = json.loads(self._versions_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_versions(self, versions: list[dict]) -> None:
        self._versions_path.parent.mkdir(parents=True, exist_ok=True)
        self._versions_path.write_text(
            json.dumps(versions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_input_versions(self) -> dict:
        versions = self._load_versions()
        return {"versions": versions, "count": len(versions)}

    def publish_input_version(self, version_id: str | None = None) -> dict:
        versions = self._load_versions()

        if version_id:
            target = next((v for v in versions if v["version_id"] == version_id), None)
            if not target:
                return {"error": f"版本 {version_id} 不存在"}
            if target["status"] == "published":
                return {"error": f"版本 {version_id} 已发布"}
        else:
            gaps = self.collection_gaps()
            now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            vid = f"v_{now_str}_{uuid.uuid4().hex[:6]}"
            target = {
                "version_id": vid,
                "label": f"自动快照 {now_str}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "published_at": None,
                "country_count": len(self._all_countries_cn),
                "gap_remaining": gaps["summary"]["total_gaps"],
                "status": "draft",
            }
            versions.append(target)

        for v in versions:
            if v["status"] == "published":
                v["status"] = "archived"

        target["status"] = "published"
        target["published_at"] = datetime.now(timezone.utc).isoformat()

        self._save_versions(versions)
        return {"published": target}
