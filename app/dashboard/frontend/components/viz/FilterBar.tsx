"use client";

interface SelectOption { label: string; value: string; }

interface FilterBarProps {
  search?: { value: string; onChange: (v: string) => void; placeholder?: string };
  selects?: Array<{ label: string; value: string; options: SelectOption[]; onChange: (v: string) => void }>;
  stats?: Array<{ label: string; value: string | number }>;
}

export default function FilterBar({ search, selects, stats }: FilterBarProps) {
  return (
    <div style={{
      background: "var(--color-bg-card)",
      border: "1px solid var(--color-border)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm) var(--space-md)",
      marginBottom: "var(--space-md)",
      display: "flex",
      flexWrap: "wrap",
      alignItems: "center",
      gap: "var(--space-sm)",
    }}>
      {search && (
        <input
          type="text"
          value={search.value}
          onChange={(e) => search.onChange(e.target.value)}
          placeholder={search.placeholder ?? "搜索…"}
          style={{ minWidth: 160, flex: "0 1 200px" }}
        />
      )}
      {selects?.map((s, i) => (
        <label key={i} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--color-text-secondary)" }}>
          {s.label}
          <select value={s.value} onChange={(e) => s.onChange(e.target.value)}>
            {s.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </label>
      ))}
      {stats && stats.length > 0 && (
        <div style={{ marginLeft: "auto", display: "flex", gap: "var(--space-md)", fontSize: 12 }}>
          {stats.map((s, i) => (
            <span key={i} style={{ color: "var(--color-text-muted)" }}>
              {s.label} <strong style={{ color: "var(--color-primary)" }}>{s.value}</strong>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
