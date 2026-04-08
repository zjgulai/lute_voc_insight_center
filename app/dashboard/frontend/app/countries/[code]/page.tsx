"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "../../../lib/api";

interface CountryDetail {
  country: { code: string; name_cn: string; is_top20: boolean; is_top10: boolean; sales_amount: number | null };
  personas: Record<string, unknown>[];
  purchasing_power: Record<string, unknown>[];
  trust_sources: Record<string, unknown>[];
  platforms: Record<string, unknown>[];
  keywords: Record<string, unknown>[];
  voc_summary: Record<string, unknown>[];
  brand_voc_summary?: Record<string, unknown>[];
}

export default function CountryDetailPage() {
  const params = useParams();
  const code = (params?.code as string)?.toUpperCase() || "";
  const [data, setData] = useState<CountryDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!code) return;
    api.countryDetail(code).then((d) => setData(d as unknown as CountryDetail)).catch((e) => setError(e.message));
  }, [code]);

  if (error) return <div className="alert-error">{error}</div>;
  if (!data) return <div className="loading-text">加载 {code} 数据...</div>;

  const { country, personas, purchasing_power, trust_sources, platforms, keywords, brand_voc_summary } = data;

  return (
    <>
      <div className="page-header">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)" }}>
          <Link href="/countries" style={{ fontSize: 13 }}>← 返回国家列表</Link>
        </div>
        <h1 className="page-title" style={{ marginTop: "var(--space-sm)" }}>
          {country.code} — {country.name_cn}
        </h1>
        <div className="row" style={{ gap: "var(--space-xs)", marginTop: "var(--space-xs)" }}>
          {country.is_top20 && <span className="badge badge-success">TOP20</span>}
          {country.is_top10 && <span className="badge badge-info">TOP10</span>}
          {country.sales_amount != null && (
            <span className="badge badge-neutral">
              销售额: {country.sales_amount.toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* Personas */}
      {personas.length > 0 && (
        <div>
          <div className="card-title" style={{ marginBottom: "var(--space-md)" }}>用户画像 ({personas.length} 条品线)</div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))",
            gap: "var(--space-md)",
            marginBottom: "var(--space-lg)",
          }}>
            {personas.map((p, i) => (
              <div key={i} className="persona-card">
                <div className="persona-card-header">
                  {p.product_line as string}
                </div>
                <div className="persona-fields">
                  <div className="persona-field">
                    <div className="persona-field-label">身份画像</div>
                    <div className="persona-field-value">{(p.identity_profile as string) || "—"}</div>
                  </div>
                  <div className="persona-field">
                    <div className="persona-field-label">购买习惯</div>
                    <div className="persona-field-value">{(p.purchase_habit as string) || "—"}</div>
                  </div>
                  <div className="persona-field">
                    <div className="persona-field-label">品牌偏好</div>
                    <div className="persona-field-value">{(p.brand_preference as string) || "—"}</div>
                  </div>
                  <div className="persona-field">
                    <div className="persona-field-label">核心竞品</div>
                    <div className="persona-field-value">{(p.competitor_brands as string) || "—"}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Purchasing Power */}
      {purchasing_power.length > 0 && (
        <div className="card">
          <div className="card-title">购买力与价格敏感 ({purchasing_power.length} 条)</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>品线</th>
                  <th>购买力层级</th>
                  <th>品类支出心智</th>
                  <th>价格敏感方式</th>
                  <th>优先级</th>
                </tr>
              </thead>
              <tbody>
                {purchasing_power.map((pp, i) => (
                  <tr key={i}>
                    <td>{pp.product_line as string}</td>
                    <td>
                      <span className="badge badge-info">
                        {pp.purchasing_power_tier as string}
                      </span>
                    </td>
                    <td className="text-sm">{(pp.spending_mindset as string)?.slice(0, 100)}</td>
                    <td className="text-sm">{(pp.price_sensitivity as string)?.slice(0, 100)}</td>
                    <td>
                      <span className="badge badge-success">{pp.priority as string}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Platforms */}
      {platforms.length > 0 && (
        <div className="card">
          <div className="card-title">平台入口 ({platforms.length} 个)</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>平台</th>
                  <th>类型</th>
                  <th>入口/版块</th>
                  <th>访问方式</th>
                </tr>
              </thead>
              <tbody>
                {platforms.map((pl, i) => (
                  <tr key={i}>
                    <td className="font-semibold">{pl.platform as string}</td>
                    <td>
                      <span className="badge badge-info">{pl.platform_type as string}</span>
                    </td>
                    <td className="text-sm">{pl.entry_section as string}</td>
                    <td className="text-sm">{pl.access_method as string}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Trust Sources */}
      {trust_sources.length > 0 && (
        <div className="card">
          <div className="card-title">信息源质量分层 ({trust_sources.length} 条)</div>
          <div className="table-wrap" style={{ maxHeight: 400, overflowY: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>品线</th>
                  <th>来源层级</th>
                  <th>来源类型</th>
                  <th>来源名称</th>
                  <th>链接</th>
                </tr>
              </thead>
              <tbody>
                {trust_sources.map((ts, i) => (
                  <tr key={i}>
                    <td>{ts.product_line as string}</td>
                    <td>
                      <span className="badge badge-warning">{ts.source_tier as string}</span>
                    </td>
                    <td className="text-sm">{ts.source_type as string}</td>
                    <td className="text-sm">{ts.source_name as string}</td>
                    <td>
                      {ts.url ? (
                        <a href={ts.url as string} target="_blank" rel="noopener noreferrer" className="text-sm">
                          链接
                        </a>
                      ) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Keywords */}
      {keywords.length > 0 && (
        <div className="card">
          <div className="card-title">品线关键词 ({keywords.length} 条)</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>品线</th>
                  <th>销售额</th>
                  <th>国家内占比</th>
                  <th>品线排名</th>
                  <th>抓取优先级</th>
                </tr>
              </thead>
              <tbody>
                {keywords.map((kw, i) => (
                  <tr key={i}>
                    <td className="font-semibold">{kw.product_line as string}</td>
                    <td className="font-mono">
                      {kw.sales_amount != null ? Number(kw.sales_amount).toLocaleString() : "—"}
                    </td>
                    <td>{kw.share_in_country as string}</td>
                    <td>{String(kw.line_rank ?? "—")}</td>
                    <td>
                      <span className="badge badge-success">{kw.crawl_priority as string}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Brand VOC Summary */}
      {(brand_voc_summary ?? []).length > 0 && (
        <div className="card">
          <div className="card-title">品牌 VOC 概览 ({(brand_voc_summary ?? []).length} 条)</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>品线</th>
                  <th>品牌</th>
                  <th>证据条数</th>
                  <th>频次合计</th>
                  <th>高强度占比</th>
                  <th>Top痛点</th>
                  <th>Top主题</th>
                </tr>
              </thead>
              <tbody>
                {(brand_voc_summary ?? []).slice(0, 50).map((row, i) => (
                  <tr key={i}>
                    <td>{String(row.product_line ?? "")}</td>
                    <td className="font-semibold">{String(row.competitor_brand ?? "")}</td>
                    <td>{Number(row.total_records ?? 0)}</td>
                    <td>{Number(row.frequency_sum ?? 0)}</td>
                    <td>{Number(row.high_intensity_pct ?? 0)}%</td>
                    <td>{String(row.top_pain_category ?? "")}</td>
                    <td className="text-sm">{String(row.top_negative_themes ?? "")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
