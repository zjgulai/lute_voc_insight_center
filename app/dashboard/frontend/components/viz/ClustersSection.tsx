"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import FilterBar from "./FilterBar";
import { HeatmapMatrix, InsightCallout } from "../insights";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const ClustersSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const clusterData = data.clusters as R[];
  const segments = (data.segments ?? []) as R[];
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("top20");

  const filtered = useMemo(() => {
    let rows = clusterData;
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((c) =>
        s(c.cluster).toLowerCase().includes(q) ||
        s(c.representative_countries).toLowerCase().includes(q)
      );
    }
    if (sort === "top20") rows = [...rows].sort((a, b) => n(b.top20_count) - n(a.top20_count));
    else rows = [...rows].sort((a, b) => s(a.cluster).localeCompare(s(b.cluster)));
    return rows;
  }, [clusterData, search, sort]);

  const pieData = filtered.map((c) => ({
    name: s(c.cluster), value: n(c.top20_count) || 1,
  }));

  // Heatmap: Cluster × representative countries
  const clusterNames = filtered.map((c) => s(c.cluster));
  const allReps = new Set<string>();
  filtered.forEach((c) => {
    const reps = s(c.representative_countries).split(/[、,，]/).map((r) => r.trim()).filter(Boolean);
    reps.forEach((r) => allReps.add(r));
  });
  const repCountries = Array.from(allReps).slice(0, 12);
  const heatCells = clusterNames.flatMap((cl) => {
    const row = filtered.find((c) => s(c.cluster) === cl);
    const reps = row ? s(row.representative_countries).split(/[、,，]/).map((r) => r.trim()) : [];
    return repCountries.map((rc) => ({
      row: cl, column: rc, value: reps.includes(rc) ? 1 : 0,
      label: reps.includes(rc) ? "覆盖" : undefined,
    }));
  });

  // Bar: cluster coverage breadth
  const barData = filtered.map((c) => ({
    name: s(c.cluster).slice(0, 12),
    top20: n(c.top20_count),
    countries: s(c.representative_countries).split(/[、,，]/).filter(Boolean).length,
  }));

  return (
    <section id="clusters" ref={ref} className="viz-section">
      <h2 className="viz-section-title">区域 Cluster 策略</h2>

      <FilterBar
        search={{ value: search, onChange: setSearch, placeholder: "搜索 Cluster/国家…" }}
        selects={[
          { label: "排序", value: sort, options: [
            { label: "TOP20数", value: "top20" }, { label: "名称", value: "name" },
          ], onChange: setSort },
        ]}
        stats={[
          { label: "Cluster", value: filtered.length },
          { label: "代表国家", value: allReps.size },
        ]}
      />

      <div className="dual-grid">
        <div className="viz-chart-container">
          <div className="card-title">Cluster 分布</div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name }) => name} animationDuration={800}>
                {pieData.map((_, idx) => <Cell key={idx} fill={CHART_COLORS_RAW[idx % CHART_COLORS_RAW.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="viz-chart-container">
          <div className="card-title">Cluster 覆盖广度</div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-30} textAnchor="end" height={60} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="top20" name="TOP20国家" fill={CHART_COLORS_RAW[0]} radius={[4, 4, 0, 0]} animationDuration={800} />
              <Bar dataKey="countries" name="代表国家" fill={CHART_COLORS_RAW[1]} radius={[4, 4, 0, 0]} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {repCountries.length > 0 && (
        <>
          <HeatmapMatrix
            title="Cluster × 代表国家结构"
            description="查看各 Cluster 间代表国家的重叠度"
            rows={clusterNames}
            columns={repCountries}
            cells={heatCells}
            formatValue={(v) => v > 0 ? "✓" : ""}
          />
          <InsightCallout
            title="Cluster 结构洞察"
            summary="如果多个 Cluster 共享相同代表国家，说明该国家在不同策略维度都有代表性，是跨 Cluster 的枢纽市场。"
            bullets={[
              "同列多个 ✓ 的国家适合做首批试点",
              "独占一列的国家可能有独特市场特征",
            ]}
            badge="结构分析"
          />
        </>
      )}

      <div className="viz-chart-container" style={{ marginTop: "var(--space-md)" }}>
        <div className="card-title">Cluster 策略概览</div>
        <div className="table-wrap" style={{ maxHeight: 300, overflowY: "auto" }}>
          <table>
            <thead><tr><th>Cluster</th><th>代表国家</th><th>渠道侧重</th><th>建议动作</th></tr></thead>
            <tbody>
              {filtered.map((c, i) => (
                <tr key={i}>
                  <td className="font-semibold">{s(c.cluster)}</td>
                  <td className="text-sm">{s(c.representative_countries).slice(0, 50)}</td>
                  <td className="text-sm">{s(c.channel_focus).slice(0, 40)}</td>
                  <td className="text-sm">{s(c.recommended_actions).slice(0, 60)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
});

ClustersSection.displayName = "ClustersSection";
export default ClustersSection;
