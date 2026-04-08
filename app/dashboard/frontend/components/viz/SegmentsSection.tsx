"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import FilterBar from "./FilterBar";
import { HeatmapMatrix, WeightedWordCloud, InsightCallout } from "../insights";
import type { WeightedWord } from "../insights";
import { extractInsightTerms } from "../../lib/insightText";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }

function s(v: unknown): string { return String(v ?? ""); }

const SegmentsSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const segments = (data.segments ?? []) as R[];
  const [search, setSearch] = useState("");
  const [cluster, setCluster] = useState("全部");
  const [product, setProduct] = useState("全部");
  const [priority, setPriority] = useState("全部");
  const [sort, setSort] = useState("priority");

  const clusterOptions = useMemo(() => {
    const set = new Set(segments.map((r) => s(r.region_cluster)).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [segments]);

  const productOptions = useMemo(() => {
    const set = new Set(segments.map((r) => s(r.product_line)).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [segments]);

  const filtered = useMemo(() => {
    let rows = segments;
    if (cluster !== "全部") rows = rows.filter((r) => s(r.region_cluster) === cluster);
    if (product !== "全部") rows = rows.filter((r) => s(r.product_line) === product);
    if (priority !== "全部") rows = rows.filter((r) => s(r.priority) === priority);
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((r) =>
        s(r.country).toLowerCase().includes(q) ||
        s(r.segment_name).toLowerCase().includes(q) ||
        s(r.core_pain_points).toLowerCase().includes(q)
      );
    }
    if (sort === "priority") rows = [...rows].sort((a, b) => s(a.priority).localeCompare(s(b.priority)));
    else if (sort === "country") rows = [...rows].sort((a, b) => s(a.country).localeCompare(s(b.country)));
    else rows = [...rows].sort((a, b) => s(a.segment_name).localeCompare(s(b.segment_name)));
    return rows;
  }, [segments, cluster, product, priority, search, sort]);

  const p0Count = filtered.filter((r) => s(r.priority) === "P0").length;
  const countryCount = new Set(filtered.map((r) => s(r.country_code))).size;

  // Heatmap: Cluster × Priority
  const heatClusters = Array.from(new Set(filtered.map((r) => s(r.region_cluster)).filter(Boolean)));
  const heatPriorities = ["P0", "P1", "P2", "P3"];
  const heatCells = heatClusters.flatMap((cl) =>
    heatPriorities.map((pr) => ({
      row: cl, column: pr,
      value: filtered.filter((r) => s(r.region_cluster) === cl && s(r.priority) === pr).length,
    }))
  );

  // Lifecycle bar
  const lcMap: Record<string, number> = {};
  filtered.forEach((r) => {
    const lc = s(r.lifecycle) || "未知";
    lcMap[lc] = (lcMap[lc] || 0) + 1;
  });
  const lcData = Object.entries(lcMap).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);

  // Word cloud from pain points, resistance, trust
  const wordMap = new Map<string, { weight: number; tone: WeightedWord["tone"]; meta: string }>();
  for (const row of filtered) {
    for (const term of extractInsightTerms(s(row.core_pain_points))) {
      const e = wordMap.get(term) ?? { weight: 0, tone: "strong" as const, meta: "痛点" };
      e.weight += 1; wordMap.set(term, e);
    }
    for (const term of extractInsightTerms(s(row.main_resistance))) {
      const e = wordMap.get(term) ?? { weight: 0, tone: "default" as const, meta: "阻力" };
      e.weight += 1; wordMap.set(term, e);
    }
    for (const term of extractInsightTerms(s(row.core_trust_source))) {
      const e = wordMap.get(term) ?? { weight: 0, tone: "muted" as const, meta: "信任" };
      e.weight += 1; wordMap.set(term, e);
    }
  }
  const words: WeightedWord[] = Array.from(wordMap.entries())
    .map(([text, d]) => ({ text, weight: d.weight, tone: d.tone, meta: d.meta }))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 40);

  return (
    <section id="segments" ref={ref} className="viz-section">
      <h2 className="viz-section-title">客群矩阵</h2>

      <FilterBar
        search={{ value: search, onChange: setSearch, placeholder: "搜索国家/客群/痛点…" }}
        selects={[
          { label: "Cluster", value: cluster, options: clusterOptions, onChange: setCluster },
          { label: "品线", value: product, options: productOptions, onChange: setProduct },
          { label: "优先级", value: priority, options: [
            { label: "全部", value: "全部" }, { label: "P0", value: "P0" },
            { label: "P1", value: "P1" }, { label: "P2", value: "P2" }, { label: "P3", value: "P3" },
          ], onChange: setPriority },
          { label: "排序", value: sort, options: [
            { label: "优先级", value: "priority" }, { label: "国家", value: "country" }, { label: "客群", value: "segment" },
          ], onChange: setSort },
        ]}
        stats={[
          { label: "记录", value: filtered.length },
          { label: "国家", value: countryCount },
          { label: "P0", value: p0Count },
        ]}
      />

      <div className="stat-grid">
        <div className="stat-card"><div className="stat-value">{filtered.length}</div><div className="stat-label">客群记录</div></div>
        <div className="stat-card"><div className="stat-value">{countryCount}</div><div className="stat-label">覆盖国家</div></div>
        <div className="stat-card"><div className="stat-value">{new Set(filtered.map((r) => s(r.region_cluster))).size}</div><div className="stat-label">Cluster</div></div>
        <div className="stat-card"><div className="stat-value">{p0Count}</div><div className="stat-label">P0 客群</div></div>
      </div>

      {heatClusters.length > 0 && (
        <>
          <HeatmapMatrix
            title="Cluster × 优先级分布"
            description="行=区域Cluster，列=优先级，数值=客群记录数"
            rows={heatClusters}
            columns={heatPriorities}
            cells={heatCells}
          />
          <InsightCallout
            title="热力图解读"
            summary="如果某个 Cluster 在 P0 列密度最高，说明该区域有最多高优先级客群，适合优先投入资源。"
            bullets={[
              "P0 密集区域建议优先布局全渠道运营",
              "P2/P3 区域可作为观察或后期拓展方向",
            ]}
            badge="策略建议"
          />
        </>
      )}

      <div className="dual-grid" style={{ marginTop: "var(--space-md)" }}>
        <div className="viz-chart-container">
          <div className="card-title">生命周期分布</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={lcData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill={CHART_COLORS_RAW[0]} radius={[4, 4, 0, 0]} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <WeightedWordCloud title="客群痛点·阻力·信任词云" description="红=痛点，绿=阻力，蓝=信任来源" words={words} />
      </div>

      <div className="viz-chart-container" style={{ marginTop: "var(--space-md)" }}>
        <div className="card-title">客群明细（前 30 条）</div>
        <div className="table-wrap" style={{ maxHeight: 400, overflowY: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>国家</th><th>品线</th><th>客群</th><th>生命周期</th>
                <th>优先级</th><th>核心痛点</th><th>信任来源</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 30).map((r, i) => (
                <tr key={i}>
                  <td>{s(r.country)}</td>
                  <td className="text-sm">{s(r.product_line)}</td>
                  <td className="font-semibold text-sm">{s(r.segment_name)}</td>
                  <td className="text-sm">{s(r.lifecycle)}</td>
                  <td><span className={`badge ${s(r.priority) === "P0" ? "badge-error" : s(r.priority) === "P1" ? "badge-warning" : "badge-neutral"}`}>{s(r.priority)}</span></td>
                  <td className="text-xs" style={{ maxWidth: 180 }}>{s(r.core_pain_points).slice(0, 60)}</td>
                  <td className="text-xs" style={{ maxWidth: 120 }}>{s(r.core_trust_source).slice(0, 40)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
});

SegmentsSection.displayName = "SegmentsSection";
export default SegmentsSection;
