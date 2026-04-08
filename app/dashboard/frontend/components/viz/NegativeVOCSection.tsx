"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo, Fragment } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import FilterBar from "./FilterBar";
import { HeatmapMatrix, WeightedWordCloud, InsightCallout } from "../insights";
import type { WeightedWord } from "../insights";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; filterCountry?: string; filterProductLine?: string; filterBrand?: string; }
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const PAIN_CATEGORIES = ["功能", "价格", "体验", "服务", "安全"];
const PAIN_CATEGORY_COLORS: Record<string, string> = {
  "功能": CHART_COLORS_RAW[1], "体验": CHART_COLORS_RAW[2],
  "价格": CHART_COLORS_RAW[3], "服务": CHART_COLORS_RAW[4], "安全": CHART_COLORS_RAW[5],
};
const INTENSITY_COLOR: Record<string, string> = {
  "高": "var(--color-error)", "中": "var(--color-warning)", "低": "var(--color-text-muted)",
};
const PLATFORM_TYPE_LABELS: Record<string, string> = {
  competitor_dtc: "竞品DTC", third_party_review: "第三方评测",
  social_media: "社媒", vertical_community: "垂类社区",
  vertical_official: "垂类官媒", ecommerce: "电商平台",
  search_engine: "搜索引擎", other: "其他",
};
const PAGE_SIZE = 30;

const NegativeVOCSection = forwardRef<HTMLElement, Props>(({ data, filterCountry: extCountry, filterProductLine: extLine, filterBrand: extBrand }, ref) => {
  const rawVocNeg = (data.voc_negative ?? []) as R[];
  const vocNeg = useMemo(() => {
    let rows = rawVocNeg;
    if (extCountry && extCountry !== "all") rows = rows.filter((r) => s(r.country) === extCountry);
    if (extLine && extLine !== "all") rows = rows.filter((r) => s(r.product_line) === extLine);
    if (extBrand && extBrand !== "all") rows = rows.filter((r) => s(r.competitor_brand) === extBrand);
    return rows;
  }, [rawVocNeg, extCountry, extLine, extBrand]);

  const [filterCountry, setFilterCountry] = useState("all");
  const [filterLine, setFilterLine] = useState("all");
  const [filterPlatform, setFilterPlatform] = useState("all");
  const [filterSubcat, setFilterSubcat] = useState("all");
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [page, setPage] = useState(0);

  const countryOptions = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.country)).filter(Boolean));
    return [{ label: "全部国家", value: "all" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [vocNeg]);
  const lineOptions = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.product_line)).filter(Boolean));
    return [{ label: "全部品线", value: "all" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [vocNeg]);
  const platformOptions = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.platform)).filter(Boolean));
    return [{ label: "全部平台", value: "all" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [vocNeg]);
  const subcatOptions = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.pain_subcategory)).filter((v) => v && v !== "其他"));
    return [{ label: "全部子分类", value: "all" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [vocNeg]);

  const filtered = useMemo(() => {
    let result = vocNeg;
    if (filterCountry !== "all") result = result.filter((r) => s(r.country) === filterCountry);
    if (filterLine !== "all") result = result.filter((r) => s(r.product_line) === filterLine);
    if (filterPlatform !== "all") result = result.filter((r) => s(r.platform) === filterPlatform);
    if (filterSubcat !== "all") result = result.filter((r) => s(r.pain_subcategory) === filterSubcat);
    return result;
  }, [vocNeg, filterCountry, filterLine, filterPlatform, filterSubcat]);

  if (vocNeg.length === 0) {
    return (
      <section id="vocnegative" ref={ref} className="viz-section">
        <h2 className="viz-section-title">痛点深挖</h2>
        <div className="empty-state">负面 VOC 数据待采集</div>
      </section>
    );
  }

  const painBarData = PAIN_CATEGORIES.map((cat) => ({
    name: cat,
    freq: filtered.filter((r) => s(r.pain_category) === cat).reduce((sum, r) => sum + (n(r.frequency) || 1), 0),
  })).sort((a, b) => b.freq - a.freq);

  const subcatBarData = useMemo(() => {
    const map: Record<string, { name: string; freq: number; parent: string }> = {};
    filtered.forEach((r) => {
      const sc = s(r.pain_subcategory);
      if (!sc || sc === "其他") return;
      const parent = s(r.pain_category);
      if (!map[sc]) map[sc] = { name: sc, freq: 0, parent };
      map[sc].freq += n(r.frequency) || 1;
    });
    return Object.values(map).sort((a, b) => b.freq - a.freq).slice(0, 15);
  }, [filtered]);

  const wordMap = new Map<string, number>();
  filtered.forEach((r) => {
    const theme = s(r.negative_theme) || s(r.pain_subcategory);
    if (theme && theme !== "其他") wordMap.set(theme, (wordMap.get(theme) || 0) + (n(r.frequency) || 1));
  });
  const negWords: WeightedWord[] = Array.from(wordMap.entries())
    .map(([text, weight]) => ({ text, weight, tone: "strong" as const }))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 30);

  const totalFreq = filtered.reduce((sum, r) => sum + (n(r.frequency) || 1), 0);
  const highIntensity = filtered.filter((r) => s(r.intensity) === "高").length;
  const topPain = painBarData[0]?.name ?? "—";
  const topSubcat = subcatBarData[0]?.name ?? "—";

  const heatCountries = Array.from(new Set(filtered.map((r) => s(r.country)).filter(Boolean))).slice(0, 12);
  const heatPainCells = heatCountries.flatMap((c) =>
    PAIN_CATEGORIES.map((cat) => ({
      row: c,
      column: cat,
      value: filtered.filter((r) => s(r.country) === c && s(r.pain_category) === cat).reduce((sum, r) => sum + (n(r.frequency) || 1), 0),
    }))
  );

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pagedRows = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <section id="vocnegative" ref={ref} className="viz-section">
      <h2 className="viz-section-title">痛点深挖</h2>

      <FilterBar
        selects={[
          { label: "国家", value: filterCountry, options: countryOptions, onChange: setFilterCountry },
          { label: "品线", value: filterLine, options: lineOptions, onChange: setFilterLine },
          { label: "平台", value: filterPlatform, options: platformOptions, onChange: setFilterPlatform },
          { label: "子分类", value: filterSubcat, options: subcatOptions, onChange: setFilterSubcat },
        ]}
        stats={[
          { label: "条目", value: filtered.length },
          { label: "频次", value: totalFreq },
          { label: "高强度", value: highIntensity },
        ]}
      />

      <div className="stat-grid">
        <div className="stat-card"><div className="stat-value">{filtered.length}</div><div className="stat-label">负面条目</div></div>
        <div className="stat-card"><div className="stat-value">{totalFreq}</div><div className="stat-label">频次合计</div></div>
        <div className="stat-card"><div className="stat-value" style={{ color: "var(--color-error)" }}>{highIntensity}</div><div className="stat-label">高强度</div></div>
        <div className="stat-card"><div className="stat-value">{topPain}</div><div className="stat-label">TOP 痛点大类</div></div>
        <div className="stat-card"><div className="stat-value" style={{ fontSize: 18 }}>{topSubcat}</div><div className="stat-label">TOP 子分类</div></div>
      </div>

      <div className="dual-grid">
        <div className="viz-chart-container">
          <div className="card-title">痛点大类分布</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={painBarData} layout="vertical" margin={{ left: 50 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={45} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="freq" name="频次" fill={CHART_COLORS_RAW[3]} radius={[0, 4, 4, 0]} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <WeightedWordCloud title="痛点主题词云" description="词越大频次越高" words={negWords} />
      </div>

      {subcatBarData.length > 0 && (
        <div className="viz-chart-container">
          <div className="card-title">品线痛点子分类拆解</div>
          <ResponsiveContainer width="100%" height={Math.max(260, subcatBarData.length * 28)}>
            <BarChart data={subcatBarData} layout="vertical" margin={{ left: 120 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={115} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="freq" name="频次" radius={[0, 4, 4, 0]} animationDuration={800}>
                {subcatBarData.map((entry) => (
                  <rect key={entry.name} fill={PAIN_CATEGORY_COLORS[entry.parent] || CHART_COLORS_RAW[0]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", gap: "var(--space-md)", justifyContent: "center", marginTop: "var(--space-sm)", fontSize: 11 }}>
            {PAIN_CATEGORIES.map((cat) => (
              <span key={cat} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: PAIN_CATEGORY_COLORS[cat] }} />
                {cat}
              </span>
            ))}
          </div>
        </div>
      )}

      {heatCountries.length > 0 && (
        <HeatmapMatrix
          title="国家 x 痛点大类 热力图"
          description="数值 = 频次，颜色越深该国该类痛点越集中"
          rows={heatCountries}
          columns={PAIN_CATEGORIES}
          cells={heatPainCells}
        />
      )}

      <div className="viz-chart-container" style={{ overflowX: "auto" }}>
        <div className="card-title">负面条目明细</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>国家</th><th>品线</th><th>平台</th><th>痛点</th>
                <th>子分类</th><th>主题</th><th>强度</th><th>频次</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              {pagedRows.map((r, i) => {
                const globalIdx = page * PAGE_SIZE + i;
                const themeDisplay = s(r.negative_theme) || s(r.pain_subcategory) || "—";
                return (
                  <Fragment key={globalIdx}>
                    <tr>
                      <td>{s(r.country)}</td>
                      <td>{s(r.product_line)}</td>
                      <td>{s(r.platform)}</td>
                      <td>{s(r.pain_category)}</td>
                      <td style={{ fontSize: 12 }}>{s(r.pain_subcategory) || "—"}</td>
                      <td style={{ fontSize: 12 }}>{themeDisplay}</td>
                      <td><span style={{ color: INTENSITY_COLOR[s(r.intensity)] || "inherit", fontWeight: 600 }}>{s(r.intensity)}</span></td>
                      <td>{n(r.frequency) || 1}</td>
                      <td>
                        <button
                          style={{ fontSize: 11, padding: "2px 6px", cursor: "pointer" }}
                          onClick={() => setExpandedIdx(expandedIdx === globalIdx ? null : globalIdx)}
                        >
                          {expandedIdx === globalIdx ? "收起" : "展开"}
                        </button>
                      </td>
                    </tr>
                    {expandedIdx === globalIdx && (
                      <tr>
                        <td colSpan={9} style={{ background: "var(--color-bg-card-alt)", fontSize: 12, lineHeight: 1.8 }}>
                          <div><strong>原文:</strong> {s(r.original_text)}</div>
                          {s(r.translated_text) ? (
                            <div><strong>中译:</strong> {s(r.translated_text)}</div>
                          ) : (
                            <div style={{ color: "var(--color-text-muted)" }}><strong>中译:</strong> 翻译待补充</div>
                          )}
                          {s(r.competitor_brand) && <div><strong>竞品:</strong> {s(r.competitor_brand)}</div>}
                          {s(r.action_suggestion) && <div><strong>建议:</strong> {s(r.action_suggestion)}</div>}
                          <div style={{ color: "var(--color-text-muted)", marginTop: 4 }}>
                            <span>来源: {PLATFORM_TYPE_LABELS[s(r.platform_type)] || s(r.platform_type)}</span>
                            {s(r.batch_code) && <span style={{ marginLeft: 12 }}>批次: {s(r.batch_code)}</span>}
                            {s(r.collect_date) && <span style={{ marginLeft: 12 }}>日期: {s(r.collect_date)}</span>}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 8, marginTop: 8, fontSize: 12 }}>
            <button disabled={page === 0} onClick={() => { setPage(page - 1); setExpandedIdx(null); }} style={{ padding: "2px 8px", cursor: "pointer" }}>上一页</button>
            <span style={{ color: "var(--color-text-muted)" }}>{page + 1} / {totalPages}（共 {filtered.length} 条）</span>
            <button disabled={page >= totalPages - 1} onClick={() => { setPage(page + 1); setExpandedIdx(null); }} style={{ padding: "2px 8px", cursor: "pointer" }}>下一页</button>
          </div>
        )}
      </div>

      <InsightCallout
        title="痛点深挖洞察"
        summary={`当前范围共 ${filtered.length} 条负面记录，频次合计 ${totalFreq}。高强度占 ${filtered.length > 0 ? Math.round((highIntensity / filtered.length) * 100) : 0}%，最集中的大类为「${topPain}」，最集中的子分类为「${topSubcat}」。`}
        bullets={[
          `「${topSubcat}」是品线维度最突出的痛点子分类，频次 ${subcatBarData[0]?.freq || 0}`,
          `功能类和体验类合计占负面声量的 ${painBarData.filter((p) => p.name === "功能" || p.name === "体验").reduce((s, p) => s + p.freq, 0)} 频次`,
          subcatBarData.length > 1
            ? `排名前三的子分类为：${subcatBarData.slice(0, 3).map((d) => d.name).join("、")}`
            : "数据量较少，建议扩大采集范围",
        ]}
        badge="痛点深挖"
      />
    </section>
  );
});

NegativeVOCSection.displayName = "NegativeVOCSection";
export default NegativeVOCSection;
