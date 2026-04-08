"use client";
import type { VizDataset } from "../../lib/api";
import { api } from "../../lib/api";
import { forwardRef, useMemo, useState, useEffect } from "react";

type R = Record<string, unknown>;
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const PAIN_CATEGORY_COLORS: Record<string, string> = {
  "功能": "#3b82f6", "体验": "#f59e0b", "价格": "#ef4444",
  "服务": "#8b5cf6", "安全": "#ec4899",
};

interface Props { data: VizDataset; filterCountry?: string; filterProductLine?: string; }

const OpportunitySummarySection = forwardRef<HTMLElement, Props>(({ data, filterCountry, filterProductLine }, ref) => {
  const rawVocNeg = ((data as unknown as R).voc_negative ?? []) as R[];
  const vocNeg = useMemo(() => {
    let rows = rawVocNeg;
    if (filterCountry && filterCountry !== "all") rows = rows.filter((r) => s(r.country) === filterCountry);
    if (filterProductLine && filterProductLine !== "all") rows = rows.filter((r) => s(r.product_line) === filterProductLine);
    return rows;
  }, [rawVocNeg, filterCountry, filterProductLine]);
  const platforms = (data.platforms ?? []) as R[];
  const timeline = ((data as unknown as R).voc_timeline ?? []) as R[];
  const compMeta = (data as unknown as R).competitor_ingest_meta as R | undefined;

  const insights = useMemo(() => {
    if (vocNeg.length === 0) return [];

    const painCounts: Record<string, number> = {};
    const subcatCounts: Record<string, number> = {};
    const brandCounts: Record<string, number> = {};
    const platformCounts: Record<string, number> = {};
    let highIntensity = 0;

    vocNeg.forEach((r) => {
      const pc = s(r.pain_category);
      const sc = s(r.pain_subcategory);
      const brand = s(r.competitor_brand);
      const plat = s(r.platform);
      const freq = n(r.frequency) || 1;
      if (pc) painCounts[pc] = (painCounts[pc] || 0) + freq;
      if (sc && sc !== "其他") subcatCounts[sc] = (subcatCounts[sc] || 0) + freq;
      if (brand) brandCounts[brand] = (brandCounts[brand] || 0) + freq;
      if (plat) platformCounts[plat] = (platformCounts[plat] || 0) + 1;
      if (s(r.intensity) === "高") highIntensity++;
    });

    const topPain = Object.entries(painCounts).sort((a, b) => b[1] - a[1])[0];
    const topSubcat = Object.entries(subcatCounts).sort((a, b) => b[1] - a[1])[0];
    const topBrand = Object.entries(brandCounts).sort((a, b) => b[1] - a[1])[0];
    const topPlatform = Object.entries(platformCounts).sort((a, b) => b[1] - a[1])[0];
    const countryCoverage = new Set(vocNeg.map((r) => s(r.country)).filter(Boolean)).size;
    const brandCount = Object.keys(brandCounts).length;
    const hiPct = vocNeg.length > 0 ? Math.round((highIntensity / vocNeg.length) * 100) : 0;

    const result = [];

    if (topPain && topSubcat) {
      result.push({
        icon: "target",
        title: "核心痛点",
        text: `${topPain[0]}类痛点频次最高（${topPain[1]}次），其中「${topSubcat[0]}」最集中（${topSubcat[1]}次）`,
        color: PAIN_CATEGORY_COLORS[topPain[0]] || "#6b7280",
        priority: "high" as const,
      });
    }

    if (topBrand) {
      result.push({
        icon: "users",
        title: "竞品弱点",
        text: `${topBrand[0]} 负面反馈最集中（频次 ${topBrand[1]}），共 ${brandCount} 个品牌被提及`,
        color: "#8b5cf6",
        priority: "high" as const,
      });
    }

    if (topPlatform) {
      result.push({
        icon: "map",
        title: "渠道覆盖",
        text: `核心声量集中于 ${topPlatform[0]}（${topPlatform[1]} 条），覆盖 ${countryCoverage} 个国家`,
        color: "#06b6d4",
        priority: "medium" as const,
      });
    }

    if (timeline.length > 0) {
      const periods = Array.from(new Set(timeline.map((t) => s(t.period)))).sort();
      result.push({
        icon: "trend",
        title: "趋势信号",
        text: `已采集 ${periods.length} 个时间批次，可追踪痛点演变趋势`,
        color: "#f59e0b",
        priority: "medium" as const,
      });
    }

    result.push({
      icon: "data",
      title: "数据覆盖",
      text: `本次分析覆盖 ${Object.keys(platformCounts).length} 个平台、${brandCount} 个竞品品牌、${vocNeg.length} 条负面记录，高强度占 ${hiPct}%`,
      color: "#10b981",
      priority: "info" as const,
    });

    return result;
  }, [vocNeg, timeline]);

  const priorityMatrix = useMemo(() => {
    const subcatMap: Record<string, { freq: number; highCount: number; countries: Set<string>; painCat: string }> = {};
    vocNeg.forEach((r) => {
      const sc = s(r.pain_subcategory);
      if (!sc || sc === "其他") return;
      if (!subcatMap[sc]) subcatMap[sc] = { freq: 0, highCount: 0, countries: new Set(), painCat: s(r.pain_category) };
      subcatMap[sc].freq += n(r.frequency) || 1;
      if (s(r.intensity) === "高") subcatMap[sc].highCount++;
      const c = s(r.country);
      if (c) subcatMap[sc].countries.add(c);
    });
    return Object.entries(subcatMap)
      .map(([name, d]) => ({
        name,
        painCategory: d.painCat,
        frequency: d.freq,
        severity: d.freq > 0 ? Math.round((d.highCount / Math.max(1, d.freq)) * 100) : 0,
        coverage: d.countries.size,
      }))
      .sort((a, b) => b.frequency - a.frequency);
  }, [vocNeg]);

  const ICON_MAP: Record<string, string> = {
    target: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 4a6 6 0 1 1 0 12 6 6 0 0 1 0-12zm0 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4z",
    users: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm13 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
    map: "M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4zm7-4v16m8-12v16",
    trend: "M22 12h-4l-3 9L9 3l-3 9H2",
    data: "M18 20V10M12 20V4M6 20v-6",
  };

  if (vocNeg.length === 0) {
    return (
      <section id="opp-summary" ref={ref} className="viz-section">
        <h2 className="viz-section-title">机会点摘要</h2>
        <div className="empty-state">负面 VOC 数据待采集，完成采集后将自动生成机会点摘要</div>
      </section>
    );
  }

  return (
    <section id="opp-summary" ref={ref} className="viz-section">
      <h2 className="viz-section-title">机会点摘要</h2>
      <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "var(--space-lg)" }}>
        基于 {vocNeg.length} 条负面 VOC 数据自动提炼的核心结论，按优先级排序
      </p>

      <div style={{ display: "grid", gap: "var(--space-md)", marginBottom: "var(--space-xl)" }}>
        {insights.map((item, i) => (
          <div
            key={i}
            className="card"
            style={{
              padding: "var(--space-md) var(--space-lg)",
              display: "flex",
              alignItems: "flex-start",
              gap: "var(--space-md)",
              borderLeft: `4px solid ${item.color}`,
            }}
          >
            <div style={{
              width: 36, height: 36, borderRadius: "var(--radius-md)",
              background: `${item.color}15`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={item.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d={ICON_MAP[item.icon] || ICON_MAP.data} />
              </svg>
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: item.color, marginBottom: 2 }}>{item.title}</div>
              <div style={{ fontSize: 14, color: "var(--color-text)", lineHeight: 1.6 }}>{item.text}</div>
            </div>
          </div>
        ))}
      </div>

      {priorityMatrix.length > 0 && (
        <div className="card" style={{ padding: "var(--space-lg)" }}>
          <div className="card-title">痛点子分类优先级矩阵</div>
          <p style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: "var(--space-md)" }}>
            按频次排序，展示各子分类的严重程度（高强度占比）和覆盖范围（国家数）
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>痛点子分类</th>
                  <th>所属大类</th>
                  <th>频次</th>
                  <th>高强度占比</th>
                  <th>覆盖国家</th>
                  <th>优先级</th>
                </tr>
              </thead>
              <tbody>
                {priorityMatrix.slice(0, 12).map((item) => {
                  const priority = item.frequency > 50 && item.severity > 30 ? "P0"
                    : item.frequency > 20 ? "P1"
                    : item.frequency > 5 ? "P2" : "P3";
                  const priorityColor = { P0: "var(--color-error)", P1: "var(--color-warning)", P2: "var(--color-info)", P3: "var(--color-text-muted)" }[priority];
                  return (
                    <tr key={item.name}>
                      <td style={{ fontWeight: 600, fontSize: 13 }}>{item.name}</td>
                      <td>
                        <span style={{
                          fontSize: 11, padding: "1px 8px", borderRadius: "var(--radius-sm)",
                          background: `${PAIN_CATEGORY_COLORS[item.painCategory] || "#6b7280"}18`,
                          color: PAIN_CATEGORY_COLORS[item.painCategory] || "#6b7280",
                          fontWeight: 600,
                        }}>
                          {item.painCategory}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{item.frequency}</td>
                      <td>{item.severity}%</td>
                      <td>{item.coverage}</td>
                      <td><span style={{ fontWeight: 700, color: priorityColor }}>{priority}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
      <DeepInsightPanel filterProductLine={filterProductLine} />
    </section>
  );
});

function DeepInsightPanel({ filterProductLine }: { filterProductLine?: string }) {
  const [insight, setInsight] = useState<R | null>(null);
  const [expanded, setExpanded] = useState(false);

  const lineKey = filterProductLine === "喂养电器" ? "feedingappliance" : "breastpump";

  useEffect(() => {
    api.insightData(lineKey).then((d) => setInsight(d as R)).catch(() => setInsight(null));
  }, [lineKey]);

  if (!insight) return null;

  const fourP = (insight.framework_4p ?? {}) as R;
  const nps = (insight.nps_proxy ?? {}) as R;
  const bullets = (insight.summary_bullets ?? []) as string[];
  const competitive = (insight.competitive_intelligence ?? {}) as R;

  return (
    <div className="card" style={{ marginTop: "var(--space-lg)" }}>
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="card-title" style={{ marginBottom: 0 }}>4P 营销框架 & NPS 深度洞察</div>
        <button style={{ fontSize: 12, padding: "4px 12px" }}>{expanded ? "收起" : "展开详情"}</button>
      </div>

      {!expanded && bullets.length > 0 && (
        <div style={{ marginTop: "var(--space-md)" }}>
          {bullets.slice(0, 3).map((b, i) => (
            <div key={i} style={{
              fontSize: 13, color: "var(--color-text-secondary)", lineHeight: 1.6,
              padding: "4px 0", borderBottom: i < 2 ? "1px solid var(--color-border)" : "none",
            }}>
              {b}
            </div>
          ))}
        </div>
      )}

      {expanded && (
        <div style={{ marginTop: "var(--space-md)" }}>
          <div style={{ marginBottom: "var(--space-lg)" }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: "var(--space-sm)", color: "var(--color-primary)" }}>核心结论</div>
            {bullets.map((b, i) => (
              <div key={i} style={{ fontSize: 13, color: "var(--color-text-secondary)", lineHeight: 1.7, padding: "3px 0" }}>
                {b}
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "var(--space-md)", marginBottom: "var(--space-lg)" }}>
            {(["Product", "Price", "Place", "Promotion"] as const).map((p) => {
              const pd = (fourP[p] ?? {}) as R;
              const color = { Product: "#3b82f6", Price: "#ef4444", Place: "#8b5cf6", Promotion: "#f59e0b" }[p];
              return (
                <div key={p} style={{ padding: "var(--space-md)", background: "var(--color-bg-card-alt)", borderRadius: "var(--radius-md)", borderLeft: `4px solid ${color}` }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color, marginBottom: 6 }}>{p}</div>
                  <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 4 }}>
                    记录 {String(pd.total_records ?? 0)} | 高强度 {String(pd.high_intensity_ratio ?? 0)}%
                  </div>
                  <div style={{ fontSize: 12, lineHeight: 1.5 }}>{String(pd.insight ?? "—")}</div>
                  <div style={{ fontSize: 11, color: "var(--color-primary)", marginTop: 6, fontWeight: 600 }}>{String(pd.recommendation ?? "")}</div>
                </div>
              );
            })}
          </div>

          {nps.by_brand != null && (
            <div style={{ marginBottom: "var(--space-lg)" }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: "var(--space-sm)" }}>NPS 代理得分（按品牌）</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>品牌</th><th>综合分</th><th>功能</th><th>体验</th><th>价格</th><th>服务</th></tr>
                  </thead>
                  <tbody>
                    {Object.entries((nps.brand_detail ?? {}) as Record<string, R>)
                      .sort((a, b) => n(a[1].composite) - n(b[1].composite))
                      .map(([brand, detail]) => (
                        <tr key={brand}>
                          <td style={{ fontWeight: 600 }}>{brand}</td>
                          <td style={{ fontWeight: 700, color: n(detail.composite) < 60 ? "var(--color-error)" : "var(--color-success)" }}>
                            {n(detail.composite).toFixed(1)}
                          </td>
                          <td>{n(detail.functional).toFixed(0)}</td>
                          <td>{n(detail.experience).toFixed(0)}</td>
                          <td>{n(detail.price_perception).toFixed(0)}</td>
                          <td>{n(detail.service).toFixed(0)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: "var(--space-sm)" }}>
                {String(nps.insight ?? "")}
              </div>
            </div>
          )}

          {competitive.brand_vulnerability_matrix != null && (
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: "var(--space-sm)" }}>竞品脆弱性矩阵</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>品牌</th><th>总量</th><th>高强度比</th><th>功能</th><th>体验</th><th>价格</th><th>服务</th><th>安全</th></tr>
                  </thead>
                  <tbody>
                    {Object.entries((competitive.brand_vulnerability_matrix as Record<string, R>) ?? {})
                      .sort((a, b) => n(b[1].high_ratio) - n(a[1].high_ratio))
                      .map(([brand, v]) => (
                        <tr key={brand}>
                          <td style={{ fontWeight: 600 }}>{brand}</td>
                          <td>{String(v.total)}</td>
                          <td style={{ fontWeight: 600, color: n(v.high_ratio) > 30 ? "var(--color-error)" : "inherit" }}>{String(v.high_ratio)}%</td>
                          <td>{String(v["功能"])}</td>
                          <td>{String(v["体验"])}</td>
                          <td>{String(v["价格"])}</td>
                          <td>{String(v["服务"])}</td>
                          <td>{String(v["安全"])}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

OpportunitySummarySection.displayName = "OpportunitySummarySection";
export default OpportunitySummarySection;
