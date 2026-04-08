"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import FilterBar from "./FilterBar";
import { CHART_COLORS_RAW } from "./constants";

type R = Record<string, unknown>;
interface Props { data: VizDataset; filterCountry?: string; filterProductLine?: string; filterBrand?: string; }
function s(v: unknown): string { return String(v ?? ""); }
function n(v: unknown): number { return typeof v === "number" ? v : 0; }

const PAIN_COLORS: Record<string, string> = {
  "功能": CHART_COLORS_RAW[1],
  "体验": CHART_COLORS_RAW[2],
  "价格": CHART_COLORS_RAW[3],
  "服务": CHART_COLORS_RAW[4],
  "安全": CHART_COLORS_RAW[5],
};

const METRIC_OPTIONS = [
  { label: "负面条目数", value: "count" },
  { label: "频次合计", value: "frequency" },
  { label: "高强度占比", value: "high_intensity_pct" },
];

const TimelineTrendSection = forwardRef<HTMLElement, Props>(({ data, filterCountry: extCountry, filterProductLine: extLine, filterBrand: extBrand }, ref) => {
  const rawTimeline = ((data as unknown as Record<string, unknown>).voc_timeline ?? []) as R[];
  const timeline = useMemo(() => {
    let rows = rawTimeline;
    if (extCountry && extCountry !== "all") rows = rows.filter((r) => s(r.country) === extCountry);
    if (extLine && extLine !== "all") rows = rows.filter((r) => s(r.product_line) === extLine);
    if (extBrand && extBrand !== "all") rows = rows.filter((r) => s(r.competitor_brand) === extBrand);
    return rows;
  }, [rawTimeline, extCountry, extLine, extBrand]);
  const [filterCountry, setFilterCountry] = useState("all");
  const [filterLine, setFilterLine] = useState("all");
  const [metric, setMetric] = useState("count");

  const countryOptions = useMemo(() => {
    const set = new Set(timeline.map((r) => s(r.country)).filter(Boolean));
    return [{ label: "全部国家", value: "all" }, ...Array.from(set).map((v) => ({ label: v, value: v }))];
  }, [timeline]);

  const lineOptions = useMemo(() => {
    const set = new Set(timeline.map((r) => s(r.product_line)).filter(Boolean));
    return [{ label: "全部品线", value: "all" }, ...Array.from(set).map((v) => ({ label: v, value: v }))];
  }, [timeline]);

  const filtered = useMemo(() => {
    let result = timeline;
    if (filterCountry !== "all") result = result.filter((r) => s(r.country) === filterCountry);
    if (filterLine !== "all") result = result.filter((r) => s(r.product_line) === filterLine);
    return result;
  }, [timeline, filterCountry, filterLine]);

  const painCategories = useMemo(() => {
    return Array.from(new Set(filtered.map((r) => s(r.pain_category)).filter(Boolean)));
  }, [filtered]);

  const chartData = useMemo(() => {
    const periodMap: Record<string, Record<string, number>> = {};
    for (const r of filtered) {
      const period = s(r.period);
      const pain = s(r.pain_category);
      if (!period || !pain) continue;
      if (!periodMap[period]) periodMap[period] = {};
      const count = n(r.count);
      const freq = n(r.frequency);
      const highInt = count > 0 ? (n(r.high_intensity_count) / count) * 100 : 0;
      const val = metric === "count" ? count : metric === "frequency" ? freq : highInt;
      periodMap[period][pain] = (periodMap[period][pain] || 0) + val;
    }
    return Object.entries(periodMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([period, pains]) => ({ period, ...pains }));
  }, [filtered, metric]);

  const totalRecords = filtered.reduce((sum, r) => sum + n(r.count), 0);

  return (
    <section id="timeline" ref={ref} className="viz-section">
      <h2 className="viz-section-title">负面 VOC 时间趋势</h2>

      <FilterBar
        search={{ value: "", onChange: () => {}, placeholder: "" }}
        selects={[
          { label: "国家", value: filterCountry, options: countryOptions, onChange: setFilterCountry },
          { label: "品线", value: filterLine, options: lineOptions, onChange: setFilterLine },
          { label: "指标", value: metric, options: METRIC_OPTIONS, onChange: setMetric },
        ]}
        stats={[
          { label: "时间点", value: chartData.length },
          { label: "痛点类", value: painCategories.length },
          { label: "总条目", value: totalRecords },
        ]}
      />

      {chartData.length > 0 ? (
        <div className="viz-chart-container">
          <div className="card-title">
            {METRIC_OPTIONS.find((o) => o.value === metric)?.label || metric} × 痛点类别趋势
          </div>
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {painCategories.map((pain) => (
                <Line
                  key={pain}
                  type="monotone"
                  dataKey={pain}
                  name={pain}
                  stroke={PAIN_COLORS[pain] || CHART_COLORS_RAW[0]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  animationDuration={800}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="card" style={{ padding: "var(--space-lg)", textAlign: "center", color: "var(--color-text-secondary)" }}>
          当前筛选条件下无时间线数据。随采集批次增多，此区域将展示多时间点趋势对比。
        </div>
      )}
    </section>
  );
});

TimelineTrendSection.displayName = "TimelineTrendSection";
export default TimelineTrendSection;
