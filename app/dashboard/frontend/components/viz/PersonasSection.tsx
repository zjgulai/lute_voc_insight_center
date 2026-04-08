import type { VizDataset } from "../../lib/api";
import { forwardRef } from "react";
import { Treemap, ResponsiveContainer } from "recharts";
import { CHART_COLORS_RAW } from "./constants";

interface Props {
  data: VizDataset;
}

const PersonasSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const lineCount: Record<string, number> = {};
  for (const p of data.personas) {
    const line = (p.product_line as string) || "unknown";
    lineCount[line] = (lineCount[line] || 0) + 1;
  }
  const treeData = Object.entries(lineCount).map(([name, size]) => ({ name, size }));

  return (
    <section id="personas" ref={ref} className="viz-section">
      <h2 className="viz-section-title">用户画像 — 品线分布</h2>
      <div className="viz-chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <Treemap
            data={treeData}
            dataKey="size"
            nameKey="name"
            stroke="var(--color-bg-card)"
            animationDuration={600}
            content={({ x, y, width, height, name, index }: {
              x: number; y: number; width: number; height: number;
              name: string; index: number;
            }) => (
              <g>
                <rect
                  x={x} y={y} width={width} height={height}
                  fill={CHART_COLORS_RAW[(index ?? 0) % CHART_COLORS_RAW.length]}
                  rx={4}
                />
                {width > 60 && height > 30 && (
                  <text
                    x={x + width / 2}
                    y={y + height / 2}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill="#fff"
                    fontSize={12}
                    fontWeight={600}
                  >
                    {name}
                  </text>
                )}
              </g>
            )}
          />
        </ResponsiveContainer>
      </div>
    </section>
  );
});

PersonasSection.displayName = "PersonasSection";
export default PersonasSection;
