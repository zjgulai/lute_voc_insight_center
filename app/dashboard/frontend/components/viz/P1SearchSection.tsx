"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useState, useMemo } from "react";

type R = Record<string, unknown>;
interface Props { data: VizDataset; }
function s(v: unknown): string { return String(v ?? ""); }

const P1SearchSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const p1 = (data.p1_search ?? []) as R[];
  const countries = Array.from(new Set(p1.map((r) => s(r.country))));
  const [tab, setTab] = useState(countries[0] ?? "");

  const items = useMemo(() => p1.filter((r) => s(r.country) === tab), [p1, tab]);

  return (
    <section id="p1search" ref={ref} className="viz-section">
      <h2 className="viz-section-title">P1 搜索作业单</h2>

      <div className="stat-grid">
        <div className="stat-card"><div className="stat-value">{p1.length}</div><div className="stat-label">P1 组合数</div></div>
        <div className="stat-card"><div className="stat-value">{countries.length}</div><div className="stat-label">覆盖国家</div></div>
        <div className="stat-card"><div className="stat-value">{new Set(p1.map((r) => s(r.product_line))).size}</div><div className="stat-label">品线数</div></div>
      </div>

      <div className="tabs">
        {countries.map((c) => (
          <button key={c} className="tab" data-active={tab === c} onClick={() => setTab(c)}>
            {c}
          </button>
        ))}
      </div>

      {items.map((item, i) => (
        <div key={i} className="card" style={{ marginBottom: "var(--space-md)" }}>
          <div className="card-title">{s(item.product_line)}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-md)" }}>
            <div>
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>站内搜索词</div>
              <p className="text-sm">{s(item.site_search_query) || "—"}</p>
            </div>
            <div>
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>社区布尔查询</div>
              <p className="text-sm font-mono">{s(item.community_boolean_query) || "—"}</p>
            </div>
            <div>
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>本地语言变体</div>
              <p className="text-sm">{s(item.local_language_variant) || "—"}</p>
            </div>
            <div>
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>Google 搜索推荐词</div>
              <p className="text-sm font-mono">{s(item.google_search_query) || "—"}</p>
            </div>
            <div>
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>决策搜索词</div>
              <p className="text-sm">{s(item.decision_search_query) || "—"}</p>
            </div>
            <div>
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>混合测试词</div>
              <p className="text-sm">{s(item.mixed_test_terms) || "—"}</p>
            </div>
          </div>
          <div style={{ marginTop: "var(--space-md)", display: "flex", gap: "var(--space-lg)", flexWrap: "wrap" }}>
            {["entry_1", "entry_2", "entry_3"].map((key) => {
              const val = s(item[key]);
              if (!val || val === "None") return null;
              return (
                <div key={key} style={{ flex: "1 1 200px" }}>
                  <div className="text-xs text-muted" style={{ marginBottom: 2 }}>
                    {key === "entry_1" ? "入口策略 1" : key === "entry_2" ? "入口策略 2" : "入口策略 3"}
                  </div>
                  <p className="text-sm">{val.slice(0, 120)}</p>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: "var(--space-sm)", display: "flex", gap: "var(--space-sm)", flexWrap: "wrap" }}>
            <span className="badge badge-warning">{s(item.crawl_priority)}</span>
            <span className="badge badge-neutral">Rank {s(item.line_rank)}</span>
          </div>
        </div>
      ))}
      {items.length === 0 && <div className="empty-state">选择国家 Tab 查看搜索作业单</div>}
    </section>
  );
});

P1SearchSection.displayName = "P1SearchSection";
export default P1SearchSection;
