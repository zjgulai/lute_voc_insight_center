import type { VizDataset } from "../../lib/api";
import { forwardRef } from "react";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { CHART_COLORS_RAW } from "./constants";

interface Props {
  data: VizDataset;
}

const PurchasingSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const tierCount: Record<string, number> = {};
  for (const pp of data.purchasing_power) {
    const tier = (pp.purchasing_power_tier as string) || "未知";
    tierCount[tier] = (tierCount[tier] || 0) + 1;
  }
  const pieData = Object.entries(tierCount).map(([name, value]) => ({ name, value }));

  return (
    <section id="purchasing" ref={ref} className="viz-section">
      <h2 className="viz-section-title">购买力分析</h2>
      <div className="dual-grid">
        <div className="viz-chart-container">
          <div className="card-title">购买力层级分布</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={100}
                label
                animationDuration={800}
              >
                {pieData.map((_, idx) => (
                  <Cell key={idx} fill={CHART_COLORS_RAW[idx % CHART_COLORS_RAW.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="viz-chart-container">
          <div className="card-title">数据统计</div>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-value">{data.purchasing_power.length}</div>
              <div className="stat-label">购买力记录</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{pieData.length}</div>
              <div className="stat-label">购买力层级</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
});

PurchasingSection.displayName = "PurchasingSection";
export default PurchasingSection;
