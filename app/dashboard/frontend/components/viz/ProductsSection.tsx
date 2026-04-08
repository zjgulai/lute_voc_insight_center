"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import FilterBar from "./FilterBar";
import { HeatmapMatrix, InsightCallout } from "../insights";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const ProductsSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const keywords = (data.keywords ?? []) as R[];
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("全部");
  const [sort, setSort] = useState("sales");

  const filtered = useMemo(() => {
    let rows = keywords;
    if (priority !== "全部") rows = rows.filter((r) => s(r.crawl_priority) === priority);
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((r) =>
        s(r.country).toLowerCase().includes(q) ||
        s(r.product_line).toLowerCase().includes(q)
      );
    }
    if (sort === "sales") rows = [...rows].sort((a, b) => n(b.sales_amount) - n(a.sales_amount));
    else if (sort === "rank") rows = [...rows].sort((a, b) => n(a.line_rank) - n(b.line_rank));
    else rows = [...rows].sort((a, b) => s(a.product_line).localeCompare(s(b.product_line)));
    return rows;
  }, [keywords, priority, search, sort]);

  // Pie: product line sales
  const lineMap: Record<string, number> = {};
  keywords.forEach((r) => {
    const pl = s(r.product_line);
    lineMap[pl] = (lineMap[pl] || 0) + n(r.sales_amount);
  });
  const pieData = Object.entries(lineMap)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value);

  // Bar: country × line stacked
  const countryLines: Record<string, Record<string, number>> = {};
  keywords.forEach((r) => {
    const c = s(r.country); const pl = s(r.product_line);
    if (!countryLines[c]) countryLines[c] = {};
    countryLines[c][pl] = (countryLines[c][pl] || 0) + n(r.sales_amount);
  });
  const allLines = Array.from(new Set(keywords.map((r) => s(r.product_line))));
  const barData = Object.entries(countryLines)
    .map(([country, lines]) => ({ country, ...lines }))
    .sort((a, b) => {
      const ta = Object.values(a).reduce((s, v) => s + (typeof v === "number" ? v : 0), 0);
      const tb = Object.values(b).reduce((s, v) => s + (typeof v === "number" ? v : 0), 0);
      return tb - ta;
    })
    .slice(0, 10);

  // Heatmap: country × product line (based on keywords data priority)
  const heatCountries = Array.from(new Set(keywords.map((r) => s(r.country)))).slice(0, 10);
  const heatLines = allLines.slice(0, 7);
  const priorityColor: Record<string, string> = { P0: "239, 68, 68", P1: "245, 158, 11", P2: "59, 130, 246", P3: "148, 163, 184" };
  const heatCells = heatCountries.flatMap((c) =>
    heatLines.map((pl) => {
      const match = keywords.find((r) => s(r.country) === c && s(r.product_line) === pl);
      return {
        row: c, column: pl,
        value: match ? n(match.sales_amount) : 0,
        label: match ? `${s(match.crawl_priority)} — ¥${Math.round(n(match.sales_amount)).toLocaleString()}` : undefined,
        accentColor: match ? priorityColor[s(match.crawl_priority)] ?? "16, 185, 129" : undefined,
      };
    })
  );

  return (
    <section id="products" ref={ref} className="viz-section">
      <h2 className="viz-section-title">品线分析</h2>

      <FilterBar
        search={{ value: search, onChange: setSearch, placeholder: "搜索国家/品线…" }}
        selects={[
          { label: "优先级", value: priority, options: [
            { label: "全部", value: "全部" }, { label: "P1", value: "P1" }, { label: "P2", value: "P2" },
          ], onChange: setPriority },
          { label: "排序", value: sort, options: [
            { label: "销售额", value: "sales" }, { label: "排名", value: "rank" }, { label: "品线", value: "name" },
          ], onChange: setSort },
        ]}
        stats={[
          { label: "组合", value: filtered.length },
          { label: "国家", value: new Set(filtered.map((r) => s(r.country_code))).size },
          { label: "品线", value: new Set(filtered.map((r) => s(r.product_line))).size },
        ]}
      />

      <div className="dual-grid">
        <div className="viz-chart-container">
          <div className="card-title">品线销售额占比</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100}
                   innerRadius={50} label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                   animationDuration={800}>
                {pieData.map((_, idx) => <Cell key={idx} fill={CHART_COLORS_RAW[idx % CHART_COLORS_RAW.length]} />)}
              </Pie>
              <Tooltip formatter={(v) => `¥${Number(v).toLocaleString()}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="viz-chart-container">
          <div className="card-title">TOP10 国家品线销售堆叠</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData} layout="vertical" margin={{ left: 60 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="country" width={55} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `¥${Math.round(Number(v)).toLocaleString()}`} />
              {allLines.map((pl, i) => (
                <Bar key={pl} dataKey={pl} stackId="s" fill={CHART_COLORS_RAW[i % CHART_COLORS_RAW.length]} animationDuration={800} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <HeatmapMatrix
        title="国家 × 品线 优先级热力图"
        description="颜色编码: 红=P0 橙=P1 蓝=P2 灰=P3，深色表示销售额高"
        rows={heatCountries}
        columns={heatLines}
        cells={heatCells}
        formatValue={(v) => `¥${Math.round(v).toLocaleString()}`}
      />
      <InsightCallout
        title="品线热力图解读"
        summary="热力图揭示各国核心品线分布与优先级配置。高亮红色单元格代表 P0 高优先级组合。"
        bullets={[
          "P1 密集区域代表成熟市场的核心品线",
          "空白区域可能是品类拓展机会点",
        ]}
      />

      <div className="viz-chart-container" style={{ marginTop: "var(--space-md)" }}>
        <div className="card-title">品线组合明细</div>
        <div className="table-wrap" style={{ maxHeight: 350, overflowY: "auto" }}>
          <table>
            <thead>
              <tr><th>国家</th><th>品线</th><th>销售额</th><th>占比</th><th>排名</th><th>优先级</th></tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => (
                <tr key={i}>
                  <td>{s(r.country)}</td>
                  <td className="font-semibold">{s(r.product_line)}</td>
                  <td className="font-mono text-sm">¥{Math.round(n(r.sales_amount)).toLocaleString()}</td>
                  <td className="text-sm">{(Number(r.share_in_country || 0) * 100).toFixed(1)}%</td>
                  <td className="text-sm">{s(r.line_rank)}</td>
                  <td><span className={`badge ${s(r.crawl_priority) === "P1" ? "badge-warning" : "badge-neutral"}`}>{s(r.crawl_priority)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
});

ProductsSection.displayName = "ProductsSection";
export default ProductsSection;
