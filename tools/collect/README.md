# VOC 负面评论采集工具包（P0-P4 全阶段）

## 概述

母婴跨境电商 VOC 负面评论四阶段采集工具包，覆盖 TOP20 国家 × 5 品线 × 多平台 × 3 画像。
**重点支持竞品独立站（DTC）和竞品官方电商平台评论的结构化采集。**

## 目录结构

```
tools/collect/
├── competitor_registry.py         # 竞品品牌注册表（DTC域名/型号/Amazon筛选/本地化）
│
├── p0_amazon_urls.py              # P0: Amazon 1-2星 URL 生成器
├── p0_review_structurer.py        # P0: 评论结构化器（交互+JSON批量）
├── p0_seg_matcher.py              # P0: SEG画像匹配器
├── p0_batch_orchestrator.py       # P0: 批次编排器
│
├── p1_community_competitor_urls.py # P1: 社区+YouTube+竞品独立站 URL 生成器
├── p2_full_coverage_urls.py        # P2: 全覆盖URL（其余品线+第三方评测+竞品社媒）
├── p3_quality_annotator.py         # P3: 质量打分+画像匹配+竞品标准化+审核工作单
├── p4_persona_rollup.py            # P4: 四维汇总回卷 + 数据管道刷新
│
├── input/                          # JSON 批次文件投放目录
│   └── _sample_batch.json
└── output/                         # 各阶段输出
    ├── p0_amazon_urls.csv
    ├── p1_community_urls.csv
    ├── p1_competitor_dtc_urls.csv
    ├── p2_full_coverage_urls.csv
    ├── p3_review_queue.csv
    ├── p3_quality_report.txt
    └── p4_rollup_report.txt
```

## 各阶段说明

### P0: Amazon 1-2星评论直取

范围：TOP10 × 吸奶器 × Amazon

```bash
python tools/collect/p0_batch_orchestrator.py
```

### P1: 社区论坛 + 竞品独立站/官方电商

范围：
- **P1-A**: TOP10 × 喂养电器 × Reddit/Mumsnet/YouTube 等社区
- **P1-B**: TOP11-20 × 吸奶器 × YouTube + Google
- **P1-C**: TOP10 × 吸奶器+喂养电器+家居出行 × 竞品 DTC 独立站 + 竞品 Amazon 品牌筛选

```bash
python tools/collect/p1_community_competitor_urls.py
```

输出：
| 文件 | 内容 |
|------|------|
| `p1_community_urls.csv` | 社区+YouTube 搜索URL (104条) |
| `p1_competitor_dtc_urls.csv` | 竞品独立站+Amazon品牌 URL (300条) |

**竞品独立站覆盖品牌：**
- 吸奶器: Spectra, Medela, Elvie, Willow, Momcozy, Lansinoh, Motif Medical, Haakaa
- 喂养电器: Philips Avent, Tommee Tippee, Dr. Brown's, Baby Brezza, Chicco, NUK
- 家居出行: Bugaboo, UPPAbaby, Cybex, Babyzen, Graco

### P2: 全覆盖（其余品线 + 第三方评测 + 竞品社媒）

范围：
- **P2-A**: TOP20 × 家居出行/内衣服饰/智能母婴电器 × Amazon
- **P2-B**: 全品牌 × Trustpilot + Wirecutter + BabyGearLab + Which? 等评测站
- **P2-C**: 全品牌 × Instagram/Facebook 竞品社媒舆情

```bash
python tools/collect/p2_full_coverage_urls.py
```

### P3: 质量标注 + 审核

对已入库的 `dim_voc_negative_extract.csv` 进行：
- SEG 画像自动补全 / 重匹配
- 痛点大类 / 负面强度自动补全
- 竞品品牌名标准化（对齐 `competitor_registry.py`）
- 行级质量评分 (0-100)
- 低质量/低置信行输出审核工作单

```bash
python tools/collect/p3_quality_annotator.py
```

### P4: 四维汇总回卷

从明细表生成聚合表：
- `voc_summary_persona_flat.csv` ← 国家×品线×画像×痛点 四维
- `voc_summary_flat.csv` ← 国家×品线 二维

自动触发 `export_viz_json.py` + `validate_viz_dataset.py` 管道刷新。

```bash
python tools/collect/p4_persona_rollup.py
```

## 竞品品牌注册表

`competitor_registry.py` 提供统一的品牌元数据：

```python
from competitor_registry import get_brands_by_line_and_region

brands = get_brands_by_line_and_region("吸奶器", "US")
# → [Spectra, Medela, Elvie, Willow, Momcozy, Lansinoh, Motif Medical, Haakaa]
```

每个品牌包含：
| 字段 | 说明 |
|------|------|
| `brand` | 品牌名称 |
| `dtc_domain` | DTC独立站域名 |
| `dtc_review_url` | 产品评论页URL |
| `dtc_regions` | 覆盖的国家编码列表 |
| `google_review_query` | Google site: 定向搜索负面评论 |
| `amazon_brand_filter` | Amazon品牌筛选名 |
| `key_models` | 核心型号列表 |
| `local_domains` | 各国本地化域名映射 |

## 全流程数据流

```
P0: Amazon 1-2★ ─────────────┐
P1: 社区+竞品独立站 ──────────┤
P2: 第三方评测+竞品社媒 ──────┤
                              ▼
                   JSON → p0_review_structurer
                              ▼
                   dim_voc_negative_extract.csv
                              ▼
                P3: p3_quality_annotator (质量打分+审核)
                              ▼
                P4: p4_persona_rollup (四维汇总)
                              ▼
              voc_summary_persona_flat.csv (四维)
              voc_summary_flat.csv (二维)
                              ▼
                    export_viz_json.py
                              ▼
                      viz_dataset.json → 前端看板
```
