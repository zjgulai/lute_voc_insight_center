"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import FilterBar from "./FilterBar";
import { KnowledgeGraph, InsightCallout } from "../insights";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const CountriesSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const countries = data.countries;
  const personas = data.personas as R[];
  const segments = (data.segments ?? []) as R[];
  const platforms = data.platforms as R[];
  const clusters = data.clusters as R[];

  const [search, setSearch] = useState("");
  const [clusterFilter, setClusterFilter] = useState("全部");
  const [priorityFilter, setPriorityFilter] = useState("全部");
  const [sort, setSort] = useState("sales");
  const [graphCountry, setGraphCountry] = useState("US");

  const clusterMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const seg of segments) {
      const code = s(seg.country_code);
      if (code) map[code] = s(seg.region_cluster);
    }
    return map;
  }, [segments]);

  const clusterOptions = useMemo(() => {
    const set = new Set(Object.values(clusterMap).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [clusterMap]);

  const filtered = useMemo(() => {
    let rows = countries;
    if (clusterFilter !== "全部") rows = rows.filter((c) => clusterMap[c.code] === clusterFilter);
    if (priorityFilter !== "全部") {
      const topFn = priorityFilter === "TOP10" ? (c: typeof rows[0]) => c.is_top10 : (c: typeof rows[0]) => c.is_top20;
      rows = rows.filter(topFn);
    }
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((c) => c.name_cn.toLowerCase().includes(q) || c.code.toLowerCase().includes(q));
    }
    if (sort === "sales") rows = [...rows].sort((a, b) => n(b.sales_amount) - n(a.sales_amount));
    else if (sort === "name") rows = [...rows].sort((a, b) => a.name_cn.localeCompare(b.name_cn, "zh-CN"));
    else rows = [...rows].sort((a, b) => {
      const pa = personas.filter((p) => s(p.country_code) === a.code).length;
      const pb = personas.filter((p) => s(p.country_code) === b.code).length;
      return pb - pa;
    });
    return rows;
  }, [countries, clusterFilter, priorityFilter, search, sort, clusterMap, personas]);

  const barData = filtered.filter((c) => c.sales_amount).slice(0, 20)
    .map((c) => ({ name: c.name_cn, value: Math.round(n(c.sales_amount)) }));

  // Knowledge graph for selected country
  const graphNodes = useMemo(() => {
    const gc = countries.find((c) => c.code === graphCountry);
    if (!gc) return [];
    const nodes: { id: string; label: string; group: "core" | "cluster" | "product" | "segment" | "platform" }[] = [
      { id: gc.code, label: gc.name_cn, group: "core" },
    ];
    const cl = clusterMap[gc.code];
    if (cl) nodes.push({ id: `cl_${cl}`, label: cl, group: "cluster" });
    const ps = personas.filter((p) => s(p.country_code) === gc.code);
    ps.forEach((p) => {
      const pl = s(p.product_line);
      if (pl && !nodes.find((n) => n.id === `pl_${pl}`)) nodes.push({ id: `pl_${pl}`, label: pl, group: "product" });
    });
    const segs = segments.filter((sg) => s(sg.country_code) === gc.code);
    segs.slice(0, 6).forEach((sg) => {
      const sn = s(sg.segment_name);
      if (sn) nodes.push({ id: `sg_${sn}`, label: sn.slice(0, 10), group: "segment" });
    });
    const plats = platforms.filter((p) => s(p.country_code) === gc.code);
    plats.slice(0, 5).forEach((p) => {
      const pn = s(p.platform);
      if (pn && !nodes.find((n) => n.id === `pt_${pn}`)) nodes.push({ id: `pt_${pn}`, label: pn, group: "platform" });
    });
    return nodes;
  }, [graphCountry, countries, clusterMap, personas, segments, platforms]);

  const graphEdges = useMemo(() => {
    const edges: { source: string; target: string }[] = [];
    const gc = countries.find((c) => c.code === graphCountry);
    if (!gc) return edges;
    graphNodes.forEach((n) => {
      if (n.group !== "core") edges.push({ source: gc.code, target: n.id });
    });
    return edges;
  }, [graphCountry, countries, graphNodes]);

  const topCountries = countries.filter((c) => c.is_top10);

  return (
    <section id="countries" ref={ref} className="viz-section">
      <h2 className="viz-section-title">国家概览</h2>

      <FilterBar
        search={{ value: search, onChange: setSearch, placeholder: "搜索国家…" }}
        selects={[
          { label: "Cluster", value: clusterFilter, options: clusterOptions, onChange: setClusterFilter },
          { label: "级别", value: priorityFilter, options: [
            { label: "全部", value: "全部" }, { label: "TOP10", value: "TOP10" }, { label: "TOP20", value: "TOP20" },
          ], onChange: setPriorityFilter },
          { label: "排序", value: sort, options: [
            { label: "销售额", value: "sales" }, { label: "名称", value: "name" }, { label: "品线数", value: "lines" },
          ], onChange: setSort },
        ]}
        stats={[
          { label: "国家", value: filtered.length },
          { label: "TOP10", value: filtered.filter((c) => c.is_top10).length },
        ]}
      />

      <div className="viz-chart-container">
        <div className="card-title">销售额排名</div>
        <ResponsiveContainer width="100%" height={Math.max(300, barData.length * 24)}>
          <BarChart data={barData} layout="vertical" margin={{ left: 80 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v) => `¥${Number(v).toLocaleString()}`} />
            <Bar dataKey="value" fill="var(--chart-1)" radius={[0, 4, 4, 0]} animationDuration={800} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ marginTop: "var(--space-md)" }}>
        <div style={{ marginBottom: "var(--space-sm)", display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
          <strong style={{ fontSize: 14 }}>国家知识图谱</strong>
          <select value={graphCountry} onChange={(e) => setGraphCountry(e.target.value)} style={{ fontSize: 12 }}>
            {topCountries.map((c) => <option key={c.code} value={c.code}>{c.name_cn}</option>)}
          </select>
        </div>
        {graphNodes.length > 1 && (
          <KnowledgeGraph
            title={`${countries.find((c) => c.code === graphCountry)?.name_cn ?? graphCountry} — 业务关系图谱`}
            description="品线/客群/平台/Cluster 关系网络"
            nodes={graphNodes}
            edges={graphEdges}
          />
        )}
        <InsightCallout
          title="图谱解读"
          summary="从中心国家节点向外看：Cluster 定位决定运营策略，品线分布决定产品组合，客群连接决定内容方向，平台标签指引投放渠道。"
          bullets={[
            "与多品线相连的国家具有综合运营价值",
            "客群节点集中说明用户画像清晰",
          ]}
        />
      </div>
    </section>
  );
});

CountriesSection.displayName = "CountriesSection";
export default CountriesSection;
