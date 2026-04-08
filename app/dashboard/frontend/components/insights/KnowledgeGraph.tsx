"use client";
import { useMemo, useState } from "react";

type GraphNode = {
  id: string;
  label: string;
  group: "core" | "cluster" | "product" | "segment" | "platform";
  meta?: string;
};

type GraphEdge = { source: string; target: string };

interface KnowledgeGraphProps {
  title: string;
  description?: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const GROUP_COLOR: Record<string, string> = {
  core: "#111827",
  cluster: "#06b6d4",
  product: "#8b5cf6",
  segment: "#ef4444",
  platform: "#10b981",
};

const GROUP_LABEL: Record<string, string> = {
  core: "国家", cluster: "Cluster", product: "品线", segment: "客群", platform: "平台",
};

export default function KnowledgeGraph({ title, description, nodes, edges }: KnowledgeGraphProps) {
  const width = 720;
  const height = 400;
  const cx = width / 2;
  const cy = height / 2;
  const core = nodes.find((n) => n.group === "core");
  const outerNodes = nodes.filter((n) => n.group !== "core");
  const [activeId, setActiveId] = useState<string | null>(core?.id ?? null);

  const positioned = useMemo(() => {
    const map = new Map<string, GraphNode & { x: number; y: number; r: number }>();
    if (core) map.set(core.id, { ...core, x: cx, y: cy, r: 30 });
    outerNodes.forEach((n, i) => {
      const angle = (Math.PI * 2 * i) / Math.max(outerNodes.length, 1) - Math.PI / 2;
      const band = n.group === "cluster" ? 105 : n.group === "product" ? 150 : 195;
      const x = cx + Math.cos(angle) * band;
      const y = cy + Math.sin(angle) * (band * 0.72);
      const r = n.group === "cluster" ? 22 : n.group === "product" ? 18 : 14;
      map.set(n.id, { ...n, x, y, r });
    });
    return map;
  }, [core, outerNodes, cx, cy]);

  const related = useMemo(() => {
    if (!activeId) return new Set(nodes.map((n) => n.id));
    const ids = new Set([activeId]);
    edges.forEach((e) => {
      if (e.source === activeId) ids.add(e.target);
      if (e.target === activeId) ids.add(e.source);
    });
    return ids;
  }, [activeId, edges, nodes]);

  const activeNode = nodes.find((n) => n.id === activeId) ?? core ?? null;
  const activeRelations = activeNode
    ? edges
        .filter((e) => e.source === activeNode.id || e.target === activeNode.id)
        .map((e) => nodes.find((n) => n.id === (e.source === activeNode.id ? e.target : e.source)))
        .filter(Boolean)
    : [];

  return (
    <div className="card" style={{ padding: "var(--space-lg)" }}>
      <div className="card-title">{title}</div>
      {description && (
        <p className="text-sm text-secondary" style={{ marginBottom: "var(--space-md)" }}>{description}</p>
      )}
      <div style={{ display: "flex", gap: "var(--space-md)", flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 500px", minWidth: 0 }}>
          <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto" }}>
            {edges.map((e, i) => {
              const s = positioned.get(e.source);
              const t = positioned.get(e.target);
              if (!s || !t) return null;
              const active = !activeId || e.source === activeId || e.target === activeId;
              return (
                <line
                  key={i}
                  x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                  stroke={active ? "var(--color-border-hover)" : "var(--color-border)"}
                  strokeWidth={active ? 1.5 : 0.8}
                  opacity={active ? 0.7 : 0.25}
                />
              );
            })}
            {[...positioned.values()].map((n) => {
              const isActive = activeId === n.id;
              const isRelated = related.has(n.id);
              const fill = GROUP_COLOR[n.group] || "#6b7280";
              return (
                <g
                  key={n.id}
                  opacity={isRelated ? 1 : 0.3}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={() => setActiveId(n.id)}
                  onClick={() => setActiveId(n.id)}
                >
                  <circle cx={n.x} cy={n.y} r={n.r} fill={fill} opacity={0.85}
                    stroke={isActive ? "#fff" : "none"} strokeWidth={isActive ? 3 : 0}
                  />
                  <text
                    x={n.x} y={n.y + 1}
                    textAnchor="middle" dominantBaseline="central"
                    fill="#fff" fontSize={n.r > 18 ? 10 : 8} fontWeight={600}
                  >
                    {n.label.length > 6 ? `${n.label.slice(0, 6)}…` : n.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
        <div style={{ flex: "0 0 200px", fontSize: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: "var(--space-sm)" }}>关系说明</div>
          {activeNode && (
            <>
              <div style={{ marginBottom: "var(--space-sm)" }}>
                <span className="badge badge-info">{GROUP_LABEL[activeNode.group]}</span>{" "}
                <strong>{activeNode.label}</strong>
              </div>
              {activeNode.meta && (
                <p className="text-xs text-secondary" style={{ marginBottom: "var(--space-sm)" }}>{activeNode.meta}</p>
              )}
              <div style={{ fontWeight: 600, marginBottom: 4 }}>直连关系</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {activeRelations.length > 0
                  ? activeRelations.map((n) => (
                      <span key={n!.id} className="badge badge-neutral">{n!.label}</span>
                    ))
                  : <span className="text-muted text-xs">无直连</span>}
              </div>
              <button
                style={{ marginTop: "var(--space-sm)", fontSize: 11 }}
                onClick={() => setActiveId(core?.id ?? null)}
              >
                回到主节点
              </button>
            </>
          )}
          <div style={{ marginTop: "var(--space-md)", display: "flex", flexWrap: "wrap", gap: 6 }}>
            {Object.entries(GROUP_COLOR).map(([g, c]) => (
              <div key={g} style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 10 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: c, display: "inline-block" }} />
                {GROUP_LABEL[g]}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
