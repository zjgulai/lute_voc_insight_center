"use client";

import { useEffect, useState } from "react";
import { api, type Country } from "../../lib/api";
import Link from "next/link";

type Filter = "all" | "top20" | "top10";

export default function CountriesPage() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.countries().then(setCountries).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="alert-error">{error}</div>;
  if (!countries.length) return <div className="loading-text">加载国家列表...</div>;

  const filtered = countries.filter((c) => {
    if (filter === "top20" && !c.is_top20) return false;
    if (filter === "top10" && !c.is_top10) return false;
    if (search && !c.name_cn.includes(search) && !c.code.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">国家画像</h1>
        <p className="page-desc">
          点击国家查看详细的用户画像、购买力、信息源、平台入口等研究数据
        </p>
      </div>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="搜索国家..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="搜索国家"
        />
        <div className="tabs" style={{ borderBottom: "none", marginBottom: 0 }}>
          {(["all", "top20", "top10"] as Filter[]).map((f) => (
            <button
              key={f}
              className="tab"
              data-active={filter === f}
              onClick={() => setFilter(f)}
            >
              {f === "all" ? `全部 (${countries.length})` : f === "top20" ? "TOP20" : "TOP10"}
            </button>
          ))}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: "var(--space-md)",
        }}
      >
        {filtered.map((c) => (
          <Link
            key={c.code}
            href={`/countries/${c.code}`}
            className="cap-card"
            style={{ textDecoration: "none" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)", marginBottom: "var(--space-sm)" }}>
              <span style={{ fontSize: 20, fontWeight: 700, color: "var(--color-primary)" }}>
                {c.code}
              </span>
              <span style={{ fontSize: 15, fontWeight: 600 }}>{c.name_cn}</span>
            </div>
            <div className="row" style={{ gap: "var(--space-xs)" }}>
              {c.is_top20 && <span className="badge badge-success">TOP20</span>}
              {c.is_top10 && <span className="badge badge-info">TOP10</span>}
            </div>
            {c.sales_amount != null && (
              <div className="text-sm text-muted mt-sm">
                销售额: {c.sales_amount.toLocaleString()}
              </div>
            )}
          </Link>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="empty-state">未找到匹配的国家</div>
      )}
    </>
  );
}
