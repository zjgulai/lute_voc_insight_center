"use client";

interface InsightCalloutProps {
  title: string;
  summary: string;
  bullets?: string[];
  scopeNote?: string;
  badge?: string;
}

export default function InsightCallout({ title, summary, bullets = [], scopeNote, badge }: InsightCalloutProps) {
  return (
    <div
      style={{
        background: "var(--color-info-bg)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-md) var(--space-lg)",
        marginTop: "var(--space-md)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)", marginBottom: "var(--space-sm)" }}>
        <span style={{ fontSize: 16 }}>💡</span>
        <strong style={{ fontSize: 14 }}>{title}</strong>
        {badge && <span className="badge badge-info">{badge}</span>}
      </div>
      <p style={{ fontSize: 13, color: "var(--color-text-secondary)", lineHeight: 1.6, marginBottom: bullets.length > 0 ? "var(--space-sm)" : 0 }}>
        {summary}
      </p>
      {bullets.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.7 }}>
          {bullets.map((b, i) => <li key={i}>{b}</li>)}
        </ul>
      )}
      {scopeNote && (
        <p style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: "var(--space-sm)", fontStyle: "italic" }}>
          {scopeNote}
        </p>
      )}
    </div>
  );
}
