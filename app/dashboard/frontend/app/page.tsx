"use client";

import { useEffect, useState, useMemo } from "react";
import { api, API_BASE, type VizDataset, type TableInfo } from "../lib/api";

const TABLE_DESCRIPTIONS: Record<string, string> = {
  "dim_project_meta.csv": "项目元数据，关键指标与覆盖范围",
  "dim_country_product_persona.csv": "各国家×品线用户画像，含身份、购买习惯、品牌偏好",
  "dim_top20_country_insight.csv": "TOP20 国家市场洞察与负面声量",
  "dim_cluster_strategy.csv": "区域聚类策略分组",
  "dim_country_price_sensitivity.csv": "各国购买力与价格敏感度",
  "dim_info_source_quality.csv": "信源质量评级（P0-P3）",
  "cfg_top10_platform_entry.csv": "TOP10 国家平台入口与关键词包",
  "cfg_top10_country_line.csv": "TOP10 国家×品线配置",
  "cfg_p1_search_playbook.csv": "P1 优先级搜索执行作业单",
  "dim_country_segment_matrix.csv": "国家客群矩阵",
  "voc_summary_flat.csv": "VOC 汇总（痛点结构/高强度/竞品TOP3）",
  "voc_summary_persona_flat.csv": "VOC 画像汇总",
  "dim_voc_negative_extract.csv": "负面评论明细（含竞品/子分类/强度）",
};

const DASHBOARD_LABELS: Record<string, string> = {
  country_insight: "国家洞察",
  opportunity: "机会点识别",
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

const BRAND_DOMAIN: Record<string, string> = {
  Medela: "medela.com", Spectra: "spectra-baby.com", Elvie: "elvie.com",
  Willow: "willowpump.com", Momcozy: "momcozy.com", Lansinoh: "lansinoh.com",
  "Baby Buddha": "babybuddha.com", Ameda: "ameda.com",
  "Motif Medical": "motifmedical.com", Evenflo: "evenflo.com",
  "Baby Brezza": "babybrezza.com", "Tommee Tippee": "tommeetippee.com",
  "Philips Avent": "philips.com", MAM: "mambaby.com", NUK: "nuk.com",
  Chicco: "chicco.com", Bugaboo: "bugaboo.com", Uppababy: "uppababy.com",
  Graco: "gracobaby.com", "Peg Perego": "pegperego.com", Cybex: "cybex-online.com",
  Joie: "joiebaby.com", Riko: "rikochildren.com",
};

const PRODUCT_LINE_ORDER = ["吸奶器", "喂养电器", "家居出行"];
const PRODUCT_LINE_LABELS: Record<string, string> = {
  "吸奶器": "吸奶器竞品", "喂养电器": "喂养电器竞品", "家居出行": "家居出行竞品",
};

export default function OverviewPage() {
  const [data, setData] = useState<VizDataset | null>(null);
  const [tables, setTables] = useState<TableInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.vizData(),
      api.adminStatus().catch(() => null),
    ]).then(([viz, admin]) => {
      setData(viz);
      if (admin) setTables(admin.tables);
    }).catch((e) => setError(e.message));
  }, []);

  type R = Record<string, unknown>;
  const vocNeg = (((data as R | null)?.voc_negative ?? []) as R[]);
  const brandsByLine = useMemo(() => {
    const map: Record<string, Record<string, number>> = {};
    vocNeg.forEach((r) => {
      const brand = String(r.competitor_brand ?? "").trim();
      const line = String(r.product_line ?? "").trim();
      if (!brand || !line) return;
      if (!map[line]) map[line] = {};
      map[line][brand] = (map[line][brand] || 0) + 1;
    });
    return PRODUCT_LINE_ORDER
      .filter((line) => map[line] && Object.keys(map[line]).length > 0)
      .map((line) => ({
        line,
        brands: Object.entries(map[line])
          .sort((a, b) => b[1] - a[1])
          .map(([brand, count]) => ({ brand, count })),
      }));
  }, [vocNeg]);

  if (error) return <div className="alert-error">{error}</div>;
  if (!data) return <div className="loading-text">加载中...</div>;

  const { meta, overview, countries } = data;
  const top20Count = countries.filter((c) => c.is_top20).length;
  const top10Count = countries.filter((c) => c.is_top10).length;

  return (
    <>
      <section className="hero">
        <h1 className="hero-title">路特外部社媒聆听洞察中台</h1>
        <p className="hero-subtitle">
          母婴跨境电商外部社媒声音聆听与竞品洞察 — 覆盖{meta.total_countries}个国家，
          {meta.total_product_lines}条品线
        </p>
      </section>

      <div className="platform-mission">
        <div className="mission-title">中台核心使命</div>
        <div className="mission-points">
          <div>聆听外部社交媒体中真实消费者声音，系统性采集跨国、跨品线、跨平台的用户 VOC</div>
          <div>对竞品进行持续差评监测与痛点提炼，识别市场机会点，支持产品、定价、渠道与营销策略决策</div>
          <div>将分散的外部舆情数据沉淀为可复用的洞察资产，为路特品牌的本地化运营提供数据底座</div>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{meta.total_countries}</div>
          <div className="stat-label">研究国家</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{meta.total_product_lines}</div>
          <div className="stat-label">产品品线</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{top20Count}</div>
          <div className="stat-label">TOP20 国家</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{top10Count}</div>
          <div className="stat-label">TOP10 国家</div>
        </div>
      </div>

      <div className="cap-grid">
        <a href="/countries" className="cap-card">
          <div className="cap-card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          </div>
          <div className="cap-card-title">国家画像</div>
          <div className="cap-card-desc">
            按国家浏览完整研究数据，含画像、购买力、信息源、平台入口
          </div>
        </a>
        <a href="/viz" className="cap-card">
          <div className="cap-card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
          </div>
          <div className="cap-card-title">国家洞察</div>
          <div className="cap-card-desc">
            国家维度交互式看板，总览项目、国家、画像、购买力等多维度数据
          </div>
        </a>
        <a href="/opportunities" className="cap-card">
          <div className="cap-card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/></svg>
          </div>
          <div className="cap-card-title">机会点识别</div>
          <div className="cap-card-desc">
            渠道入口、VOC 声量、痛点深挖、竞品图谱与趋势追踪
          </div>
        </a>
        <a href="/admin" className="cap-card">
          <div className="cap-card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          </div>
          <div className="cap-card-title">运营后台</div>
          <div className="cap-card-desc">
            数据源管理、ETL 编排、校验与预览
          </div>
        </a>
      </div>

      {brandsByLine.length > 0 && (
        <div className="card">
          <div className="card-title">竞品品牌图谱</div>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "var(--space-md)" }}>
            点击品牌跳转至机会点识别页查看详细痛点分析
          </p>
          {brandsByLine.map(({ line, brands }) => (
            <div key={line} className="brand-section">
              <div className="brand-section-title">{PRODUCT_LINE_LABELS[line] || line}</div>
              <div className="brand-grid">
                {brands.map(({ brand, count }) => {
                  const domain = BRAND_DOMAIN[brand];
                  return (
                    <a
                      key={brand}
                      href={`/opportunities?brand=${encodeURIComponent(brand)}&line=${encodeURIComponent(line)}`}
                      className="brand-card"
                    >
                      {domain ? (
                        <img
                          src={`https://logo.clearbit.com/${domain}`}
                          alt={brand}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                            const p = (e.target as HTMLImageElement).parentElement!;
                            const fallback = document.createElement("span");
                            fallback.style.cssText = "font-size:18px;font-weight:700;color:var(--color-primary)";
                            fallback.textContent = brand.charAt(0);
                            p.insertBefore(fallback, p.firstChild);
                          }}
                        />
                      ) : (
                        <span style={{ fontSize: 18, fontWeight: 700, color: "var(--color-primary)", height: 40, display: "flex", alignItems: "center" }}>
                          {brand.charAt(0)}
                        </span>
                      )}
                      <div className="brand-name">{brand}</div>
                      <div className="brand-count">{count} 条 VOC</div>
                    </a>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {overview.length > 0 && (
        <div className="card">
          <div className="card-title">项目总览</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>指标</th>
                  <th>数值</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                {overview.map((item, i) => (
                  <tr key={i}>
                    <td>{item.key}</td>
                    <td>{String(item.value ?? "—")}</td>
                    <td style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
                      {item.desc || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-title">数据源</div>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "var(--space-md)" }}>
          看板使用以下 {tables?.length ?? meta.source_files?.length ?? 0} 个数据表构建，点击「下载」可导出原始 CSV
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>数据表</th>
                <th>备注说明</th>
                <th>行数</th>
                <th>大小</th>
                <th>更新时间</th>
                <th>看板归属</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {tables ? tables.map((t) => (
                <tr key={t.filename}>
                  <td style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 12 }}>{t.filename}</td>
                  <td style={{ fontSize: 12, color: "var(--color-text-secondary)", maxWidth: 280 }}>
                    {TABLE_DESCRIPTIONS[t.filename] || "—"}
                  </td>
                  <td>{t.exists ? t.rows.toLocaleString() : "—"}</td>
                  <td>{t.exists ? formatSize(t.size_bytes) : "—"}</td>
                  <td style={{ fontSize: 11, color: "var(--color-text-muted)" }}>
                    {t.modified_at?.slice(0, 16).replace("T", " ") || "—"}
                  </td>
                  <td>
                    {t.dashboards.map((d) => (
                      <span key={d} style={{
                        display: "inline-block", fontSize: 10, padding: "1px 6px", marginRight: 4,
                        borderRadius: "var(--radius-sm)", background: "var(--color-info-bg)",
                        border: "1px solid var(--color-border)", whiteSpace: "nowrap",
                      }}>
                        {DASHBOARD_LABELS[d] || d}
                      </span>
                    ))}
                  </td>
                  <td>
                    {t.exists && (
                      <a
                        href={`${API_BASE}/api/v1/admin/download-csv?table=${encodeURIComponent(t.filename)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          fontSize: 12, padding: "3px 10px", borderRadius: "var(--radius-sm)",
                          background: "var(--color-primary)", color: "#fff", textDecoration: "none",
                          display: "inline-block", cursor: "pointer",
                        }}
                      >
                        下载
                      </a>
                    )}
                  </td>
                </tr>
              )) : meta.source_files?.map((f, i) => (
                <tr key={i}>
                  <td style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 12 }}>{f}</td>
                  <td style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{TABLE_DESCRIPTIONS[f] || "—"}</td>
                  <td colSpan={5} style={{ fontSize: 12, color: "var(--color-text-muted)" }}>后端未连接，无法获取详细状态</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
