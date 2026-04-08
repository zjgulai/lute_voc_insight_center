"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import FilterBar from "./FilterBar";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }
function s(v: unknown): string { return String(v ?? ""); }

const TrustSourcesSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const sources = data.trust_sources as R[];
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("全部");
  const [cluster, setCluster] = useState("全部");
  const [product, setProduct] = useState("全部");
  const [tier, setTier] = useState("全部");
  const [qType, setQType] = useState("全部");

  const countryOpts = useMemo(() => {
    const set = new Set(sources.map((r) => s(r.country)).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [sources]);
  const clusterOpts = useMemo(() => {
    const set = new Set(sources.map((r) => s(r.region_cluster)).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [sources]);
  const productOpts = useMemo(() => {
    const set = new Set(sources.map((r) => s(r.product_line)).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [sources]);
  const tierOpts = useMemo(() => {
    const set = new Set(sources.map((r) => s(r.source_tier)).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [sources]);
  const qTypeOpts = useMemo(() => {
    const set = new Set(sources.map((r) => s(r.research_question_type)).filter(Boolean));
    return [{ label: "全部", value: "全部" }, ...Array.from(set).sort().map((v) => ({ label: v, value: v }))];
  }, [sources]);

  const filtered = useMemo(() => {
    let rows = sources;
    if (country !== "全部") rows = rows.filter((r) => s(r.country) === country);
    if (cluster !== "全部") rows = rows.filter((r) => s(r.region_cluster) === cluster);
    if (product !== "全部") rows = rows.filter((r) => s(r.product_line) === product);
    if (tier !== "全部") rows = rows.filter((r) => s(r.source_tier) === tier);
    if (qType !== "全部") rows = rows.filter((r) => s(r.research_question_type) === qType);
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((r) =>
        s(r.source_name).toLowerCase().includes(q) ||
        s(r.country).toLowerCase().includes(q) ||
        s(r.suggested_usage).toLowerCase().includes(q)
      );
    }
    return rows;
  }, [sources, country, cluster, product, tier, qType, search]);

  const tierCount: Record<string, number> = {};
  filtered.forEach((r) => {
    const t = s(r.source_tier) || "未知";
    tierCount[t] = (tierCount[t] || 0) + 1;
  });
  const barData = Object.entries(tierCount).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);

  return (
    <section id="trust" ref={ref} className="viz-section">
      <h2 className="viz-section-title">信息源质量分层</h2>

      <FilterBar
        search={{ value: search, onChange: setSearch, placeholder: "搜索来源名称/国家…" }}
        selects={[
          { label: "国家", value: country, options: countryOpts, onChange: setCountry },
          { label: "Cluster", value: cluster, options: clusterOpts, onChange: setCluster },
          { label: "品线", value: product, options: productOpts, onChange: setProduct },
          { label: "层级", value: tier, options: tierOpts, onChange: setTier },
          { label: "问题类型", value: qType, options: qTypeOpts, onChange: setQType },
        ]}
        stats={[
          { label: "来源", value: filtered.length },
          { label: "国家", value: new Set(filtered.map((r) => s(r.country_code))).size },
        ]}
      />

      <div className="viz-chart-container">
        <div className="card-title">来源层级分布</div>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={barData}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="var(--chart-2)" radius={[4, 4, 0, 0]} animationDuration={800} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="viz-chart-container" style={{ marginTop: "var(--space-md)" }}>
        <div className="card-title">信息源明细（前 40 条）</div>
        <div className="table-wrap" style={{ maxHeight: 400, overflowY: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>国家</th><th>品线</th><th>来源层级</th><th>来源类型</th>
                <th>来源名称</th><th>入口</th><th>建议用途</th><th>风险</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 40).map((r, i) => (
                <tr key={i}>
                  <td>{s(r.country)}</td>
                  <td className="text-sm">{s(r.product_line)}</td>
                  <td><span className={`badge ${s(r.source_tier).includes("T1") ? "badge-success" : s(r.source_tier).includes("T2") ? "badge-info" : "badge-neutral"}`}>{s(r.source_tier)}</span></td>
                  <td className="text-sm">{s(r.source_type)}</td>
                  <td className="font-semibold text-sm">{s(r.source_name).slice(0, 30)}</td>
                  <td className="text-xs">{s(r.entry).slice(0, 40)}</td>
                  <td className="text-xs">{s(r.suggested_usage).slice(0, 40)}</td>
                  <td className="text-xs text-error">{s(r.risk_notes).slice(0, 30)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
});

TrustSourcesSection.displayName = "TrustSourcesSection";
export default TrustSourcesSection;
