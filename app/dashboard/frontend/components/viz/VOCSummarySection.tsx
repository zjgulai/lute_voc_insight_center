"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import FilterBar from "./FilterBar";
import { HeatmapMatrix, WeightedWordCloud, InsightCallout } from "../insights";
import type { WeightedWord } from "../insights";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; filterCountry?: string; filterProductLine?: string; }
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const VOCSummarySection = forwardRef<HTMLElement, Props>(({ data, filterCountry: extCountry, filterProductLine: extLine }, ref) => {
  const rawVoc = (data.voc_summary ?? []) as R[];
  const voc = useMemo(() => {
    let rows = rawVoc;
    if (extCountry && extCountry !== "all") rows = rows.filter((r) => s(r.country) === extCountry);
    if (extLine && extLine !== "all") rows = rows.filter((r) => s(r.product_line) === extLine);
    return rows;
  }, [rawVoc, extCountry, extLine]);
  const rawVocPersona = (data.voc_persona_summary ?? []) as R[];
  const vocPersona = useMemo(() => {
    let rows = rawVocPersona;
    if (extCountry && extCountry !== "all") rows = rows.filter((r) => s(r.country) === extCountry);
    if (extLine && extLine !== "all") rows = rows.filter((r) => s(r.product_line) === extLine);
    return rows;
  }, [rawVocPersona, extCountry, extLine]);
  const [search, setSearch] = useState("");
  const [filterPlatform, setFilterPlatform] = useState("all");
  const [filterSegment, setFilterSegment] = useState("all");

  const platformOptions = useMemo(() => {
    const set = new Set(voc.map((r) => s(r.platform)).filter(Boolean));
    return [{ label: "全部平台", value: "all" }, ...Array.from(set).map((v) => ({ label: v, value: v }))];
  }, [voc]);

  const segmentOptions = useMemo(() => {
    const set = new Set(vocPersona.map((r) => s(r.segment_code)).filter(Boolean));
    return [{ label: "全部画像", value: "all" }, ...Array.from(set).map((v) => ({ label: v, value: v }))];
  }, [vocPersona]);

  const filtered = useMemo(() => {
    let result = voc;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((r) =>
        s(r.country).toLowerCase().includes(q) ||
        s(r.product_line).toLowerCase().includes(q)
      );
    }
    if (filterPlatform !== "all") {
      result = result.filter((r) => s(r.platform) === filterPlatform);
    }
    return result;
  }, [voc, search, filterPlatform]);

  // Bar: pain category mix by country (high_intensity_pct as severity indicator)
  const countryPain: Record<string, { func: number; price: number; exp: number; svc: number; safety: number; cnt: number }> = {};
  filtered.forEach((r) => {
    const c = s(r.country) || s(r.country_code);
    if (!countryPain[c]) countryPain[c] = { func: 0, price: 0, exp: 0, svc: 0, safety: 0, cnt: 0 };
    countryPain[c].func += n(r.pain_function_pct);
    countryPain[c].exp += n(r.pain_experience_pct);
    countryPain[c].price += n(r.pain_price_pct);
    countryPain[c].svc += n(r.pain_service_pct);
    countryPain[c].safety += n(r.pain_safety_pct);
    countryPain[c].cnt += 1;
  });
  const barData = Object.entries(countryPain)
    .filter(([k]) => k !== "全球" && k !== "GLOBAL")
    .map(([name, d]) => ({
      name,
      func: d.cnt > 0 ? Math.round(d.func / d.cnt) : 0,
      exp: d.cnt > 0 ? Math.round(d.exp / d.cnt) : 0,
      price: d.cnt > 0 ? Math.round(d.price / d.cnt) : 0,
    }))
    .sort((a, b) => (b.func + b.exp + b.price) - (a.func + a.exp + a.price))
    .slice(0, 15);

  // Heatmap: country × product line comment count
  const heatCountries = Array.from(new Set(filtered.map((r) => s(r.country) || s(r.country_code)).filter((v) => v !== "全球" && v !== "GLOBAL"))).slice(0, 12);
  const heatProducts = Array.from(new Set(filtered.map((r) => s(r.product_line)).filter(Boolean)));
  const heatCells = heatCountries.flatMap((c) =>
    heatProducts.map((pl) => {
      const matches = filtered.filter((r) => (s(r.country) || s(r.country_code)) === c && s(r.product_line) === pl);
      const total = matches.reduce((sum, r) => sum + (n(r.total_comments) || 0), 0);
      return { row: c, column: pl, value: total };
    })
  );

  // Heatmap 2: country × product_line high_intensity_pct
  const heatIntensityCells = heatCountries.flatMap((c) =>
    heatProducts.map((pl) => {
      const matches = filtered.filter((r) => (s(r.country) || s(r.country_code)) === c && s(r.product_line) === pl);
      if (matches.length === 0) return { row: c, column: pl, value: 0 };
      const weightedHigh = matches.reduce((sum, r) => sum + (n(r.high_intensity_pct) * Math.max(1, n(r.total_comments))), 0);
      const weightedBase = matches.reduce((sum, r) => sum + Math.max(1, n(r.total_comments)), 0);
      return { row: c, column: pl, value: weightedBase > 0 ? Number((weightedHigh / weightedBase).toFixed(1)) : 0 };
    })
  );

  // Platform × Segment distribution
  const filteredPersona = useMemo(() => {
    let result = vocPersona;
    if (filterSegment !== "all") result = result.filter((r) => s(r.segment_code) === filterSegment);
    if (filterPlatform !== "all") result = result.filter((r) => s(r.platform) === filterPlatform);
    return result;
  }, [vocPersona, filterSegment, filterPlatform]);

  const segPlatforms = Array.from(new Set(filteredPersona.map((r) => s(r.platform)).filter(Boolean)));
  const segCodes = Array.from(new Set(filteredPersona.map((r) => s(r.segment_code)).filter(Boolean)));
  const segPlatformCells = segPlatforms.flatMap((pl) =>
    segCodes.map((seg) => {
      const matches = filteredPersona.filter((r) => s(r.platform) === pl && s(r.segment_code) === seg);
      const total = matches.reduce((sum, r) => sum + n(r.total_comments), 0);
      return { row: pl, column: seg, value: total };
    })
  );

  // Segment negative count bar
  const segNegData = segCodes.map((seg) => {
    const matches = filteredPersona.filter((r) => s(r.segment_code) === seg);
    return { name: seg, negative: matches.reduce((sum, r) => sum + n(r.total_comments), 0) };
  }).sort((a, b) => b.negative - a.negative);

  // Split word clouds: themes and competitor brands.
  const themeMap = new Map<string, number>();
  const brandMap = new Map<string, number>();
  filtered.forEach((r) => {
    const pains = s(r.top5_negative_themes).split(";").map((t) => t.trim()).filter(Boolean);
    pains.forEach((t) => {
      themeMap.set(t, (themeMap.get(t) || 0) + 1);
    });
    const brands = s(r.top_competitor_brands).split(";").map((t) => t.trim()).filter(Boolean);
    brands.forEach((t) => {
      brandMap.set(t, (brandMap.get(t) || 0) + 1);
    });
  });
  const themeWords: WeightedWord[] = Array.from(themeMap.entries())
    .filter(([text]) => text && text !== "null" && text !== "None")
    .map(([text, weight]) => ({ text, weight, tone: "strong" as const }))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 24);
  const brandWords: WeightedWord[] = Array.from(brandMap.entries())
    .filter(([text]) => text && text !== "null" && text !== "None")
    .map(([text, weight]) => ({ text, weight, tone: "default" as const }))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 24);

  const totalComments = filtered.reduce((sum, r) => sum + n(r.total_comments), 0);
  const uniquePlatforms = new Set(filtered.map((r) => s(r.platform)).filter(Boolean)).size;

  return (
    <section id="vocsummary" ref={ref} className="viz-section">
      <h2 className="viz-section-title">VOC 评论聚合</h2>

      <FilterBar
        search={{ value: search, onChange: setSearch, placeholder: "搜索国家/品线…" }}
        selects={[
          { label: "平台", value: filterPlatform, options: platformOptions, onChange: setFilterPlatform },
          { label: "画像", value: filterSegment, options: segmentOptions, onChange: setFilterSegment },
        ]}
        stats={[
          { label: "记录", value: filtered.length },
          { label: "有效评论", value: totalComments },
          { label: "平台数", value: uniquePlatforms },
        ]}
      />

      <div className="stat-grid">
        <div className="stat-card"><div className="stat-value">{filtered.length}</div><div className="stat-label">VOC 记录</div></div>
        <div className="stat-card"><div className="stat-value">{totalComments}</div><div className="stat-label">有效评论</div></div>
        <div className="stat-card"><div className="stat-value">{new Set(filtered.map((r) => s(r.country_code))).size}</div><div className="stat-label">国家数</div></div>
        <div className="stat-card"><div className="stat-value">{uniquePlatforms}</div><div className="stat-label">平台覆盖数</div></div>
      </div>

      <div className="dual-grid">
        <div className="viz-chart-container">
          <div className="card-title">痛点结构对比 (功能/体验/价格)</div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={barData} layout="vertical" margin={{ left: 60 }}>
              <XAxis type="number" domain={[0, 100]} />
              <YAxis type="category" dataKey="name" width={55} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="func" name="功能占比" fill={CHART_COLORS_RAW[1]} stackId="r" radius={[0, 0, 0, 0]} animationDuration={800} />
              <Bar dataKey="exp" name="体验占比" fill={CHART_COLORS_RAW[2]} stackId="r" radius={[0, 0, 0, 0]} animationDuration={800} />
              <Bar dataKey="price" name="价格占比" fill={CHART_COLORS_RAW[3]} stackId="r" radius={[0, 4, 4, 0]} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <WeightedWordCloud title="负面主题词云" description="基于 TOP5 负面主题统计（证据条数）" words={themeWords} />
      </div>
      <div className="dual-grid">
        <WeightedWordCloud title="竞品品牌词云" description="基于 TOP 竞品提及统计（证据条数）" words={brandWords} />
        <div className="card" style={{ padding: "var(--space-lg)" }}>
          <div className="card-title">词云口径说明</div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary)", lineHeight: 1.8 }}>
            <div>1) 主题词云与品牌词云已拆分，避免语义混用。</div>
            <div>2) 权重按记录条目计数，主 KPI 仍是证据条数。</div>
            <div>3) 若需工单当量视角，请在内部 VOC 看板查看辅助指标。</div>
          </div>
        </div>
      </div>

      {heatCountries.length > 0 && heatProducts.length > 1 && (
        <>
          <HeatmapMatrix
            title="国家 × 品线 评论量热力图"
            description="数值=有效评论数"
            rows={heatCountries}
            columns={heatProducts}
            cells={heatCells}
          />
          <InsightCallout
            title="评论分布洞察"
            summary="热力图高亮区域表示 VOC 数据丰富度高，可优先用于深度分析。空白区域可能需要加大样本采集力度。"
            bullets={[
              "深色区域代表数据充足，分析结论可信度更高",
              "如果某品线全行空白，建议检查搜索关键词覆盖",
            ]}
            badge="数据质量"
          />
        </>
      )}

      {heatProducts.length > 1 && heatCountries.length > 0 && (
        <HeatmapMatrix
          title="国家 × 品线 高强度占比热力图"
          description="数值 = 高强度负面占比(%)，颜色越深问题越严重"
          rows={heatCountries}
          columns={heatProducts}
          cells={heatIntensityCells}
        />
      )}

      {segPlatforms.length > 0 && segCodes.length > 0 && (
        <>
          <HeatmapMatrix
            title="平台 × 画像 分布矩阵"
            description="数值 = 有效评论数，展示不同平台聚集了哪类画像用户"
            rows={segPlatforms}
            columns={segCodes}
            cells={segPlatformCells}
          />
          {segNegData.length > 0 && (
            <div className="viz-chart-container">
              <div className="card-title">画像负面评论分布</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={segNegData} layout="vertical" margin={{ left: 60 }}>
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={55} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="negative" name="负面数" fill={CHART_COLORS_RAW[3]} radius={[0, 4, 4, 0]} animationDuration={800} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </section>
  );
});

VOCSummarySection.displayName = "VOCSummarySection";
export default VOCSummarySection;
