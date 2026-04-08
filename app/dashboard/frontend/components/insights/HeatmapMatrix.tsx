"use client";
import { useState } from "react";

type HeatmapCell = {
  row: string;
  column: string;
  value: number;
  label?: string;
  meta?: string;
  accentColor?: string;
};

type HeatmapMode = "raw" | "tgi";

interface HeatmapMatrixProps {
  title: string;
  description?: string;
  rows: string[];
  columns: string[];
  cells: HeatmapCell[];
  formatValue?: (value: number) => string;
  emptyLabel?: string;
  mode?: HeatmapMode;
}

function getRawCellStyle(value: number, maxValue: number, accentColor?: string) {
  if (value <= 0 || maxValue <= 0) {
    return {
      backgroundColor: "var(--color-bg-card-alt)",
      color: "var(--color-text-muted)",
      borderColor: "var(--color-border)",
    };
  }
  const opacity = Math.max(0.18, Math.min(0.92, value / maxValue));
  const rgb = accentColor ?? "16, 185, 129";
  return {
    backgroundColor: `rgba(${rgb}, ${opacity})`,
    color: opacity > 0.5 ? "#ffffff" : "var(--color-text)",
    borderColor: `rgba(${rgb}, ${Math.min(1, opacity + 0.15)})`,
  };
}

function getTgiCellStyle(tgi: number) {
  if (tgi <= 0) {
    return {
      backgroundColor: "var(--color-bg-card-alt)",
      color: "var(--color-text-muted)",
      borderColor: "var(--color-border)",
    };
  }
  const deviation = tgi - 100;
  if (Math.abs(deviation) < 5) {
    return {
      backgroundColor: "var(--color-bg-card-alt)",
      color: "var(--color-text)",
      borderColor: "var(--color-border)",
    };
  }
  if (deviation > 0) {
    const intensity = Math.min(0.85, deviation / 100);
    return {
      backgroundColor: `rgba(239, 68, 68, ${intensity})`,
      color: intensity > 0.4 ? "#ffffff" : "var(--color-text)",
      borderColor: `rgba(239, 68, 68, ${Math.min(1, intensity + 0.15)})`,
    };
  }
  const intensity = Math.min(0.85, Math.abs(deviation) / 100);
  return {
    backgroundColor: `rgba(16, 185, 129, ${intensity})`,
    color: intensity > 0.4 ? "#ffffff" : "var(--color-text)",
    borderColor: `rgba(16, 185, 129, ${Math.min(1, intensity + 0.15)})`,
  };
}

export default function HeatmapMatrix({
  title,
  description,
  rows,
  columns,
  cells,
  formatValue,
  emptyLabel = "--",
  mode = "raw",
}: HeatmapMatrixProps) {
  const [hover, setHover] = useState<string | null>(null);
  const cellMap = new Map(cells.map((c) => [`${c.row}::${c.column}`, c]));
  const maxValue = cells.reduce((m, c) => Math.max(m, c.value), 0);

  const defaultFormat = mode === "tgi"
    ? (v: number) => v.toFixed(0)
    : (v: number) => v.toLocaleString();
  const fmt = formatValue ?? defaultFormat;

  const colAvg: Record<string, number> = {};
  if (mode === "tgi") {
    for (const col of columns) {
      const vals = rows.map((r) => cellMap.get(`${r}::${col}`)?.value ?? 0).filter((v) => v > 0);
      colAvg[col] = vals.length > 0 ? vals.reduce((s, v) => s + v, 0) / vals.length : 0;
    }
  }

  function getTgiValue(row: string, col: string, rawValue: number): number {
    const avg = colAvg[col];
    if (!avg || avg === 0 || rawValue <= 0) return 0;
    return (rawValue / avg) * 100;
  }

  return (
    <div className="card" style={{ padding: "var(--space-lg)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-sm)" }}>
        <div className="card-title" style={{ marginBottom: 0 }}>{title}</div>
        {mode === "tgi" && (
          <div style={{ display: "flex", gap: 8, fontSize: 11, alignItems: "center" }}>
            <span style={{ display: "inline-block", width: 12, height: 12, background: "rgba(16, 185, 129, 0.5)", borderRadius: 2 }} /> &lt;100 偏弱
            <span style={{ display: "inline-block", width: 12, height: 12, background: "var(--color-bg-card-alt)", border: "1px solid var(--color-border)", borderRadius: 2 }} /> ≈100 持平
            <span style={{ display: "inline-block", width: 12, height: 12, background: "rgba(239, 68, 68, 0.5)", borderRadius: 2 }} /> &gt;100 突出
          </div>
        )}
      </div>
      {description && (
        <p className="text-sm text-secondary" style={{ marginBottom: "var(--space-md)" }}>
          {description}
        </p>
      )}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th style={{ minWidth: 100 }}></th>
              {columns.map((col) => (
                <th key={col} style={{ textAlign: "center", fontSize: 11 }}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row}>
                <td style={{ fontWeight: 600, fontSize: 12, whiteSpace: "nowrap" }}>{row}</td>
                {columns.map((col) => {
                  const cell = cellMap.get(`${row}::${col}`);
                  const rawValue = cell?.value ?? 0;
                  const tgiValue = mode === "tgi" ? getTgiValue(row, col, rawValue) : rawValue;
                  const displayValue = mode === "tgi" ? tgiValue : rawValue;
                  const display = displayValue > 0 ? fmt(displayValue) : emptyLabel;
                  const style = mode === "tgi"
                    ? getTgiCellStyle(tgiValue)
                    : getRawCellStyle(rawValue, maxValue, cell?.accentColor);
                  const key = `${row}::${col}`;
                  const isHovered = hover === key;

                  return (
                    <td
                      key={col}
                      style={{
                        ...style,
                        textAlign: "center",
                        fontWeight: 600,
                        fontSize: 13,
                        cursor: "default",
                        position: "relative",
                        border: `1px solid ${style.borderColor}`,
                        transition: "transform 0.15s",
                        transform: isHovered ? "scale(1.06)" : "scale(1)",
                      }}
                      onMouseEnter={() => setHover(key)}
                      onMouseLeave={() => setHover(null)}
                    >
                      {display}
                      {isHovered && cell && (
                        <div
                          style={{
                            position: "absolute",
                            bottom: "calc(100% + 6px)",
                            left: "50%",
                            transform: "translateX(-50%)",
                            background: "var(--color-bg-card)",
                            border: "1px solid var(--color-border)",
                            borderRadius: "var(--radius-sm)",
                            padding: "6px 10px",
                            boxShadow: "var(--shadow-md)",
                            zIndex: 10,
                            minWidth: 160,
                            textAlign: "left",
                            pointerEvents: "none",
                          }}
                        >
                          <div style={{ fontWeight: 600, fontSize: 12, color: "var(--color-text)", marginBottom: 2 }}>
                            {row} / {col}
                          </div>
                          <div style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>
                            原值: {rawValue.toLocaleString()}
                            {mode === "tgi" && colAvg[col] > 0 && (
                              <> | 均值: {colAvg[col].toFixed(1)} | TGI: {tgiValue.toFixed(0)}</>
                            )}
                          </div>
                          {cell.meta && (
                            <div style={{ fontSize: 10, color: "var(--color-text-muted)", marginTop: 2 }}>
                              {cell.meta}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
