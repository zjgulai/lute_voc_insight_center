"use client";
import { useState } from "react";

export type WeightedWord = {
  text: string;
  weight: number;
  meta?: string;
  tone?: "default" | "strong" | "muted";
};

interface WeightedWordCloudProps {
  title: string;
  description?: string;
  words: WeightedWord[];
}

function getWordStyle(weight: number, maxWeight: number, tone: WeightedWord["tone"]) {
  const ratio = maxWeight > 0 ? weight / maxWeight : 0;
  const fontSize = 13 + ratio * 18;

  if (tone === "strong") {
    return {
      fontSize, background: `rgba(239, 68, 68, ${0.12 + ratio * 0.3})`, color: "#b91c1c",
    };
  }
  if (tone === "muted") {
    return {
      fontSize: fontSize - 1, background: `rgba(59, 130, 246, ${0.08 + ratio * 0.2})`, color: "#1d4ed8",
    };
  }
  return {
    fontSize, background: `rgba(16, 185, 129, ${0.1 + ratio * 0.22})`, color: "#047857",
  };
}

export default function WeightedWordCloud({ title, description, words }: WeightedWordCloudProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const maxWeight = words.reduce((m, w) => Math.max(m, w.weight), 0);
  const topWords = words.slice(0, 6);
  const toneCounts = words.reduce(
    (a, w) => { a[w.tone ?? "default"] += 1; return a; },
    { strong: 0, default: 0, muted: 0 },
  );

  return (
    <div className="card" style={{ padding: "var(--space-lg)" }}>
      <div className="card-title">{title}</div>
      {description && (
        <p className="text-sm text-secondary" style={{ marginBottom: "var(--space-md)" }}>{description}</p>
      )}

      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: "var(--space-md)", minHeight: 60 }}>
        {words.length > 0 ? words.map((w, i) => {
          const s = getWordStyle(w.weight, maxWeight, w.tone);
          return (
            <span
              key={i}
              style={{
                fontSize: s.fontSize,
                background: s.background,
                color: s.color,
                padding: "3px 10px",
                borderRadius: "var(--radius-sm)",
                fontWeight: 500,
                cursor: "default",
                position: "relative",
                transition: "transform 0.15s",
                transform: hoveredIdx === i ? "scale(1.08)" : "scale(1)",
              }}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              {w.text}
              {hoveredIdx === i && (
                <span style={{
                  position: "absolute", bottom: "calc(100% + 4px)", left: "50%", transform: "translateX(-50%)",
                  background: "var(--color-bg-card)", border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-sm)", padding: "4px 8px", boxShadow: "var(--shadow-md)",
                  fontSize: 11, whiteSpace: "nowrap", zIndex: 10, color: "var(--color-text)",
                }}>
                  <strong>{w.text}</strong> — 权重 {w.weight.toFixed(1)}
                  {w.meta && <div style={{ color: "var(--color-text-muted)", fontSize: 10 }}>{w.meta}</div>}
                </span>
              )}
            </span>
          );
        }) : (
          <span className="text-muted text-sm">暂无可生成词云的标签</span>
        )}
      </div>

      {words.length > 0 && (
        <div style={{ display: "flex", gap: "var(--space-lg)", flexWrap: "wrap", fontSize: 12 }}>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>高权重标签</div>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {topWords.map((w, i) => (
                <span key={i} className="badge badge-neutral">{w.text}</span>
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>标签图例</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 3, fontSize: 11 }}>
              <span><span style={{ color: "#b91c1c" }}>●</span> 核心主题/痛点 <strong>{toneCounts.strong}</strong></span>
              <span><span style={{ color: "#047857" }}>●</span> 决策/阻力 <strong>{toneCounts.default}</strong></span>
              <span><span style={{ color: "#1d4ed8" }}>●</span> 场景/信任 <strong>{toneCounts.muted}</strong></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
