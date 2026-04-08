"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell,
} from "recharts";
import { HeatmapMatrix, InsightCallout } from "../insights";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; filterCountry?: string; filterProductLine?: string; filterBrand?: string; }
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const PAIN_CATEGORIES = ["功能", "价格", "体验", "服务", "安全"];
const INTENSITY_RAW: Record<string, string> = { "高": "#ef4444", "中": "#f59e0b", "低": "#94a3b8" };

const CompetitorSection = forwardRef<HTMLElement, Props>(({ data, filterCountry, filterProductLine, filterBrand }, ref) => {
  const rawVocNeg = ((data as unknown as R).voc_negative ?? []) as R[];
  const vocNeg = useMemo(() => {
    let rows = rawVocNeg;
    if (filterCountry && filterCountry !== "all") rows = rows.filter((r) => s(r.country) === filterCountry);
    if (filterProductLine && filterProductLine !== "all") rows = rows.filter((r) => s(r.product_line) === filterProductLine);
    if (filterBrand && filterBrand !== "all") rows = rows.filter((r) => s(r.competitor_brand) === filterBrand);
    return rows;
  }, [rawVocNeg, filterCountry, filterProductLine, filterBrand]);

  const brands = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.competitor_brand)).filter(Boolean));
    return Array.from(set).sort();
  }, [vocNeg]);

  const brandPainData = useMemo(() => {
    return brands.map((brand) => {
      const entry: Record<string, string | number> = { brand };
      for (const cat of PAIN_CATEGORIES) {
        entry[cat] = vocNeg
          .filter((r) => s(r.competitor_brand) === brand && s(r.pain_category) === cat)
          .reduce((sum, r) => sum + (n(r.frequency) || 1), 0);
      }
      return entry;
    }).sort((a, b) => {
      const totalA = PAIN_CATEGORIES.reduce((sum, c) => sum + (a[c] as number), 0);
      const totalB = PAIN_CATEGORIES.reduce((sum, c) => sum + (b[c] as number), 0);
      return totalB - totalA;
    });
  }, [vocNeg, brands]);

  const intensityData = useMemo(() => {
    return (["高", "中", "低"] as const).map((level) => ({
      name: `${level}强度`,
      value: vocNeg.filter((r) => s(r.intensity) === level).length,
    })).filter((d) => d.value > 0);
  }, [vocNeg]);

  const brandSubcatData = useMemo(() => {
    const top5Brands = brands.slice(0, 5);
    const subcatMap: Record<string, Record<string, number>> = {};
    vocNeg.forEach((r) => {
      const brand = s(r.competitor_brand);
      const sc = s(r.pain_subcategory);
      if (!brand || !sc || sc === "其他" || !top5Brands.includes(brand)) return;
      if (!subcatMap[brand]) subcatMap[brand] = {};
      subcatMap[brand][sc] = (subcatMap[brand][sc] || 0) + (n(r.frequency) || 1);
    });
    return top5Brands.map((brand) => {
      const subs = subcatMap[brand] || {};
      return {
        brand,
        topSubcats: Object.entries(subs).sort((a, b) => b[1] - a[1]).slice(0, 3),
      };
    });
  }, [vocNeg, brands]);

  const heatCountries = useMemo(() => {
    return Array.from(new Set(vocNeg.map((r) => s(r.country)).filter(Boolean))).slice(0, 8);
  }, [vocNeg]);

  const heatBrands = useMemo(() => brands.slice(0, 8), [brands]);

  const heatCells = useMemo(() => {
    return heatBrands.flatMap((brand) =>
      heatCountries.map((country) => ({
        row: brand,
        column: country,
        value: vocNeg.filter((r) => s(r.competitor_brand) === brand && s(r.country) === country).length,
      }))
    );
  }, [vocNeg, heatBrands, heatCountries]);

  const topBrand = brandPainData[0];
  const topBrandTotal = topBrand
    ? PAIN_CATEGORIES.reduce((sum, c) => sum + ((topBrand[c] as number) || 0), 0)
    : 0;

  if (vocNeg.length === 0 || brands.length === 0) {
    return (
      <section id="competitor" ref={ref} className="viz-section">
        <h2 className="viz-section-title">竞品图谱</h2>
        <div className="empty-state">无竞品品牌数据</div>
      </section>
    );
  }

  return (
    <section id="competitor" ref={ref} className="viz-section">
      <h2 className="viz-section-title">竞品图谱</h2>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{brands.length}</div>
          <div className="stat-label">竞品品牌</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{topBrand ? String(topBrand.brand) : "—"}</div>
          <div className="stat-label">TOP 竞品</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{topBrandTotal}</div>
          <div className="stat-label">TOP 竞品频次</div>
        </div>
      </div>

      <div className="viz-chart-container">
        <div className="card-title">竞品品牌 x 痛点大类</div>
        <ResponsiveContainer width="100%" height={Math.max(240, brandPainData.length * 36)}>
          <BarChart data={brandPainData} layout="vertical" margin={{ left: 100 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="brand" width={95} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            {PAIN_CATEGORIES.map((cat, i) => (
              <Bar key={cat} dataKey={cat} stackId="pain" fill={CHART_COLORS_RAW[i]} animationDuration={800} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="dual-grid">
        {intensityData.length > 0 && (
          <div className="viz-chart-container">
            <div className="card-title">负面强度分布</div>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={intensityData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} dataKey="value" nameKey="name" label={(props) => `${props.name ?? ""} ${((props.percent ?? 0) * 100).toFixed(0)}%`}>
                  {intensityData.map((entry) => {
                    const level = entry.name.replace("强度", "") as "高" | "中" | "低";
                    return <Cell key={entry.name} fill={INTENSITY_RAW[level] || "#6b7280"} />;
                  })}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="card" style={{ padding: "var(--space-lg)" }}>
          <div className="card-title">竞品 Top3 痛点子分类</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
            {brandSubcatData.map((bd) => (
              <div key={bd.brand}>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 4 }}>{bd.brand}</div>
                <div style={{ display: "flex", gap: "var(--space-xs)", flexWrap: "wrap" }}>
                  {bd.topSubcats.map(([sc, count]) => (
                    <span key={sc} style={{
                      fontSize: 11, padding: "2px 8px", borderRadius: "var(--radius-sm)",
                      background: "var(--color-bg-card-alt)", border: "1px solid var(--color-border)",
                    }}>
                      {sc} ({count})
                    </span>
                  ))}
                  {bd.topSubcats.length === 0 && (
                    <span style={{ fontSize: 11, color: "var(--color-text-muted)" }}>无细分数据</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {heatBrands.length > 0 && heatCountries.length > 0 && (
        <HeatmapMatrix
          title="竞品品牌 x 国家 负面分布"
          description="数值 = 负面条目数，展示各品牌在不同国家被吐槽的集中度"
          rows={heatBrands}
          columns={heatCountries}
          cells={heatCells}
        />
      )}

      <InsightCallout
        title="竞品图谱洞察"
        summary={`共识别 ${brands.length} 个被提及的竞品品牌。${topBrand ? `${topBrand.brand} 负面反馈最集中（频次 ${topBrandTotal}）。` : ""}`}
        bullets={[
          "频次高的品牌代表市场讨论热度大，可作为差异化突破口",
          "多国都被提及的痛点是行业共性问题，优先解决可形成竞争优势",
        ]}
        badge="竞品洞察"
      />
    </section>
  );
});

CompetitorSection.displayName = "CompetitorSection";
export default CompetitorSection;
