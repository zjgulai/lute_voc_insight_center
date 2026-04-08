"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import FilterBar from "./FilterBar";
import { InsightCallout } from "../insights";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }
function s(v: unknown): string { return String(v ?? ""); }

const PlatformsSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const plats = data.platforms as R[];
  const countries = Array.from(new Set(plats.map((p) => s(p.country))));
  const [tab, setTab] = useState(countries[0] ?? "");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let rows = plats;
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((p) =>
        s(p.country).toLowerCase().includes(q) ||
        s(p.platform).toLowerCase().includes(q)
      );
    }
    return rows;
  }, [plats, search]);

  const typeCount: Record<string, number> = {};
  filtered.forEach((p) => {
    const t = s(p.platform_type) || "other";
    typeCount[t] = (typeCount[t] || 0) + 1;
  });
  const pieData = Object.entries(typeCount).map(([name, value]) => ({ name, value }));

  // Stacked: country × platform type
  const countryTypes: Record<string, Record<string, number>> = {};
  filtered.forEach((p) => {
    const c = s(p.country); const t = s(p.platform_type) || "other";
    if (!countryTypes[c]) countryTypes[c] = {};
    countryTypes[c][t] = (countryTypes[c][t] || 0) + 1;
  });
  const allTypes = Array.from(new Set(filtered.map((p) => s(p.platform_type) || "other")));
  const stackData = Object.entries(countryTypes)
    .map(([country, types]) => ({ country, ...types }))
    .sort((a, b) => {
      const ta = Object.values(a).reduce((s, v) => s + (typeof v === "number" ? v : 0), 0);
      const tb = Object.values(b).reduce((s, v) => s + (typeof v === "number" ? v : 0), 0);
      return tb - ta;
    });

  const tabItems = plats.filter((p) => s(p.country) === tab);
  const typeGroups: Record<string, R[]> = {};
  tabItems.forEach((p) => {
    const t = s(p.platform_type) || "other";
    if (!typeGroups[t]) typeGroups[t] = [];
    typeGroups[t].push(p);
  });

  return (
    <section id="platforms" ref={ref} className="viz-section">
      <h2 className="viz-section-title">TOP10 平台入口</h2>

      <FilterBar
        search={{ value: search, onChange: setSearch, placeholder: "搜索国家/平台…" }}
        stats={[
          { label: "平台", value: filtered.length },
          { label: "国家", value: new Set(filtered.map((p) => s(p.country_code))).size },
          { label: "类型", value: Object.keys(typeCount).length },
        ]}
      />

      <div className="dual-grid">
        <div className="viz-chart-container">
          <div className="card-title">平台类型分布</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label animationDuration={800}>
                {pieData.map((_, idx) => <Cell key={idx} fill={CHART_COLORS_RAW[idx % CHART_COLORS_RAW.length]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="viz-chart-container">
          <div className="card-title">国家 × 平台类型结构</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stackData} layout="vertical" margin={{ left: 60 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="country" width={55} tick={{ fontSize: 11 }} />
              <Tooltip />
              {allTypes.map((t, i) => (
                <Bar key={t} dataKey={t} stackId="s" fill={CHART_COLORS_RAW[i % CHART_COLORS_RAW.length]} animationDuration={800} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <InsightCallout
        title="平台结构洞察"
        summary="社媒传播类占比高的国家更适合先做内容种草和 KOL 合作，垂类社区类占比高则适合深度用户运营。"
        bullets={[
          "三种平台类型均衡的国家适合全渠道打法",
          "垂类官方媒体占比高的市场需要PR策略配合",
        ]}
      />

      <div style={{ marginTop: "var(--space-md)" }}>
        <div className="tabs">
          {countries.map((c) => (
            <button key={c} className="tab" data-active={tab === c} onClick={() => setTab(c)}>{c}</button>
          ))}
        </div>
        {Object.entries(typeGroups).map(([type, items]) => (
          <div key={type} style={{ marginBottom: "var(--space-md)" }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: "var(--space-sm)" }}>
              <span className="badge badge-info">{type}</span> ({items.length} 个平台)
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>平台</th><th>入口板块</th><th>接入方式</th><th>关键词包</th></tr></thead>
                <tbody>
                  {items.map((p, i) => (
                    <tr key={i}>
                      <td className="font-semibold">{s(p.platform)}</td>
                      <td className="text-sm">{s(p.entry_section).slice(0, 60)}</td>
                      <td className="text-sm">{s(p.access_method).slice(0, 40)}</td>
                      <td className="text-xs">{s(p.keyword_pack).slice(0, 50)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
        {tabItems.length === 0 && <div className="empty-state">选择国家 Tab 查看平台详情</div>}
      </div>
    </section>
  );
});

PlatformsSection.displayName = "PlatformsSection";
export default PlatformsSection;
