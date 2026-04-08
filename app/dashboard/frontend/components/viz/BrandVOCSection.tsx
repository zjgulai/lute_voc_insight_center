"use client";

import type { VizDataset } from "../../lib/api";
import { forwardRef, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }

function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const BrandVOCSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const rows = (data.brand_voc_summary ?? []) as R[];
  const [countryCode, setCountryCode] = useState("ALL");
  const [productLine, setProductLine] = useState("ALL");

  const countryOptions = useMemo(() => {
    const set = new Set(rows.map((r) => s(r.country_code)).filter(Boolean));
    return ["ALL", ...Array.from(set).sort()];
  }, [rows]);

  const productOptions = useMemo(() => {
    const set = new Set(rows.map((r) => s(r.product_line)).filter(Boolean));
    return ["ALL", ...Array.from(set).sort()];
  }, [rows]);

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      if (countryCode !== "ALL" && s(r.country_code) !== countryCode) return false;
      if (productLine !== "ALL" && s(r.product_line) !== productLine) return false;
      return true;
    });
  }, [rows, countryCode, productLine]);

  const barData = useMemo(() => {
    return [...filtered]
      .sort((a, b) => n(b.total_records) - n(a.total_records))
      .slice(0, 12)
      .map((r) => ({
        name: s(r.competitor_brand),
        value: n(r.total_records),
      }));
  }, [filtered]);

  return (
    <section id="brand-voc" ref={ref} className="viz-section">
      <h2 className="viz-section-title">品牌 VOC 分析</h2>
      <div style={{ display: "flex", gap: 12, marginBottom: "var(--space-md)", flexWrap: "wrap" }}>
        <label style={{ fontSize: 13 }}>
          国家
          <select value={countryCode} onChange={(e) => setCountryCode(e.target.value)} style={{ marginLeft: 8 }}>
            {countryOptions.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
          </select>
        </label>
        <label style={{ fontSize: 13 }}>
          品线
          <select value={productLine} onChange={(e) => setProductLine(e.target.value)} style={{ marginLeft: 8 }}>
            {productOptions.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
          </select>
        </label>
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--color-text-muted)" }}>
          记录数: {filtered.length}
        </span>
      </div>

      <div className="viz-chart-container">
        <div className="card-title">TOP 品牌证据条数</div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData} layout="vertical" margin={{ left: 100 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" fill="var(--chart-2)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="table-wrap" style={{ marginTop: "var(--space-md)" }}>
        <table>
          <thead>
            <tr>
              <th>国家</th>
              <th>品线</th>
              <th>品牌</th>
              <th>证据条数</th>
              <th>频次合计</th>
              <th>高强度占比</th>
              <th>Top 痛点</th>
              <th>Top 主题</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 100).map((r, i) => (
              <tr key={i}>
                <td>{s(r.country_code) || s(r.country)}</td>
                <td>{s(r.product_line)}</td>
                <td>{s(r.competitor_brand)}</td>
                <td>{n(r.total_records)}</td>
                <td>{n(r.frequency_sum)}</td>
                <td>{n(r.high_intensity_pct)}%</td>
                <td>{s(r.top_pain_category)}</td>
                <td className="text-sm">{s(r.top_negative_themes)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
});

BrandVOCSection.displayName = "BrandVOCSection";
export default BrandVOCSection;
