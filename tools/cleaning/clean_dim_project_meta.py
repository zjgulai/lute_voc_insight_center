# -*- coding: utf-8 -*-
"""清洗 dim_project_meta.csv → overview section。"""
from __future__ import annotations
from pathlib import Path
from ._common import read_csv_table, clean_str, clean_num, TABLES_DIR

_DESC_MAP: dict[str, str] = {
    "输入文件": "项目原始数据来源 Excel 文件路径",
    "输入Sheet": "使用的工作表名称",
    "原始国家×品线行数": "原始数据中国家与品线的交叉组合总数",
    "有效分析行数": "清洗后纳入分析的有效行数",
    "排除品线": "因业务需求排除不参与分析的品线",
    "TOP20国家数": "按销售额排名筛选的重点研究国家数",
    "TOP10国家数": "TOP20 中进一步聚焦的核心目标市场",
    "TOP10目标国家×品线组合数": "TOP10 国家与重点品线的有效交叉组合",
    "P1组合数": "最高优先级的可执行搜索作业组合数",
    "全量画像与媒体匹配": "全量国家用户画像与媒体平台匹配报告",
    "TOP20国家深挖": "TOP20 国家 VOC 生态深度分析报告",
    "TOP10平台入口": "TOP10 国家母婴平台入口策略清单",
    "TOP10国家×品线": "TOP10 国家×品线本地化关键词清单",
    "P1搜索作业单": "P1 组合的可执行搜索作业指令",
    "数据落表方案": "VOC 数据仓库落表结构设计方案",
    "本次综合主报告": "本次项目综合分析总报告",
    "本次综合工作簿": "多 Sheet 综合工作簿（含全部明细表）",
}


def build() -> list[dict]:
    rows = read_csv_table(TABLES_DIR / "dim_project_meta.csv")
    result = []
    for r in rows:
        key = clean_str(r.get("项目"))
        val = r.get("数值")
        if not key:
            continue
        num = clean_num(val)
        cleaned = num if num is not None else clean_str(val)
        desc = _DESC_MAP.get(key, "")
        result.append({"key": key, "value": cleaned, "desc": desc})
    return result


if __name__ == "__main__":
    import json
    data = build()
    print(f"Total: {len(data)} rows")
    print(json.dumps(data[:5], ensure_ascii=False, indent=2))
