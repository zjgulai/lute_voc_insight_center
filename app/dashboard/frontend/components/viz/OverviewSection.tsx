"use client";
import type { VizDataset } from "../../lib/api";
import { forwardRef, useMemo, useState } from "react";
import { InsightCallout } from "../insights";

type R = Record<string, unknown>;

function s(v: unknown): string {
  return String(v ?? "");
}
function n(v: unknown): number {
  return typeof v === "number" ? v : 0;
}

const PLATFORM_TYPE_LABEL: Record<string, string> = {
  social_media: "社媒传播",
  vertical_community: "垂类社区",
  vertical_official: "垂类官媒",
  ecommerce: "电商平台",
  competitor_dtc: "竞品DTC",
  third_party_review: "第三方评测",
  search_engine: "搜索引擎",
  other: "其他",
};

const PLATFORM_DOMAIN_MAP: Record<string, string> = {
  Reddit: "reddit.com",
  Instagram: "instagram.com",
  TikTok: "tiktok.com",
  "What to Expect Forums": "whattoexpect.com",
  Amazon: "amazon.com",
  Trustpilot: "trustpilot.com",
  YouTube: "youtube.com",
  Facebook: "facebook.com",
  Twitter: "twitter.com",
  Pinterest: "pinterest.com",
  BabyCenter: "babycenter.com",
  Mumsnet: "mumsnet.com",
};

function deriveTag(insight: string): string {
  if (/论坛|forum|讨论/i.test(insight)) return "论坛驱动型";
  if (/社媒|social|种草|短视频|instagram|tiktok/i.test(insight)) return "社媒种草型";
  if (/口碑|妈妈群|群|真实经验/i.test(insight)) return "口碑信任型";
  if (/权威|专家|官方|健康/i.test(insight)) return "专家权威型";
  if (/视觉|visual|图文/i.test(insight)) return "视觉内容型";
  if (/理性|功能|对比|细节/i.test(insight)) return "理性决策型";
  return "综合型";
}

function PlatformMiniCard({ name, type }: { name: string; type: string }) {
  const domain = PLATFORM_DOMAIN_MAP[name] || "";
  const faviconUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : "";
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "6px 10px", background: "var(--color-bg-card)",
      border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)",
      fontSize: 12, minWidth: 0,
    }}>
      <div style={{
        width: 24, height: 24, borderRadius: 4, background: "var(--color-bg-card-alt)",
        display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, overflow: "hidden",
      }}>
        {faviconUrl ? (
          <img src={faviconUrl} alt={name} width={16} height={16} style={{ borderRadius: 2 }}
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; (e.target as HTMLImageElement).parentElement!.textContent = name.charAt(0); }}
          />
        ) : (
          <span style={{ fontSize: 12, fontWeight: 700, color: "var(--color-primary)" }}>{name.charAt(0)}</span>
        )}
      </div>
      <span style={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</span>
    </div>
  );
}

interface Props {
  data: VizDataset;
}

const OverviewSection = forwardRef<HTMLElement, Props>(({ data }, ref) => {
  const countries = data.countries;
  const platforms = data.platforms as R[];
  const top20 = data.top20 as R[];
  const vocSummary = (data.voc_summary ?? []) as R[];

  const [filterCountry, setFilterCountry] = useState("all");
  const [filterMediaType, setFilterMediaType] = useState("all");

  const top10Countries = useMemo(() => countries.filter((c) => c.is_top10), [countries]);

  const allCountries = useMemo(() => {
    const set = new Set(platforms.map((p) => s(p.country)).filter(Boolean));
    return Array.from(set).sort();
  }, [platforms]);

  const allMediaTypes = useMemo(() => {
    const set = new Set(platforms.map((p) => s(p.platform_type)).filter(Boolean));
    return Array.from(set).sort();
  }, [platforms]);

  const matrixData = useMemo(() => {
    let rows = platforms;
    if (filterCountry !== "all") rows = rows.filter((p) => s(p.country) === filterCountry);
    if (filterMediaType !== "all") rows = rows.filter((p) => s(p.platform_type) === filterMediaType);

    const countryList = filterCountry !== "all"
      ? [filterCountry]
      : Array.from(new Set(rows.map((p) => s(p.country)).filter(Boolean))).sort();

    const mediaTypes = filterMediaType !== "all"
      ? [filterMediaType]
      : Array.from(new Set(rows.map((p) => s(p.platform_type)).filter(Boolean))).sort();

    const matrix: Record<string, Record<string, { name: string; type: string }[]>> = {};
    for (const c of countryList) matrix[c] = {};

    for (const p of rows) {
      const c = s(p.country);
      const mt = s(p.platform_type);
      const name = s(p.platform);
      if (!c || !mt || !name) continue;
      if (!matrix[c]) matrix[c] = {};
      if (!matrix[c][mt]) matrix[c][mt] = [];
      if (!matrix[c][mt].find((x) => x.name === name)) {
        matrix[c][mt].push({ name, type: mt });
      }
    }

    return { countryList, mediaTypes, matrix };
  }, [platforms, filterCountry, filterMediaType]);

  const top10Insights = useMemo(() => {
    return top10Countries.map((c) => {
      const t20 = top20.find((t) => s(t.country_code) === c.code);
      const insight = s(t20?.insight);
      const vocRows = vocSummary.filter(
        (v) => s(v.country_code) === c.code || s(v.country) === c.name_cn,
      );
      const totalComments = vocRows.reduce((sum, v) => sum + n(v.total_comments), 0);
      const highIntensityPct = vocRows.length > 0
        ? vocRows.reduce((sum, v) => sum + n(v.high_intensity_pct), 0) / vocRows.length
        : 0;
      const platformCoverage = vocRows.reduce((sum, v) => sum + n(v.platform_coverage_cnt), 0);
      const topPainCategories = vocRows.length > 0
        ? (() => {
            const pains: { label: string; pct: number }[] = [
              { label: "功能", pct: vocRows.reduce((s, v) => s + n(v.pain_function_pct), 0) / vocRows.length },
              { label: "价格", pct: vocRows.reduce((s, v) => s + n(v.pain_price_pct), 0) / vocRows.length },
              { label: "体验", pct: vocRows.reduce((s, v) => s + n(v.pain_experience_pct), 0) / vocRows.length },
              { label: "服务", pct: vocRows.reduce((s, v) => s + n(v.pain_service_pct), 0) / vocRows.length },
              { label: "安全", pct: vocRows.reduce((s, v) => s + n(v.pain_safety_pct), 0) / vocRows.length },
            ];
            return pains.filter((p) => p.pct > 0).sort((a, b) => b.pct - a.pct).slice(0, 3);
          })()
        : [];
      const tag = deriveTag(insight);
      const negThemes = s(t20?.top_negative_themes);
      const negVolume = s(t20?.negative_volume);
      return { code: c.code, name: c.name_cn, insight, totalComments, highIntensityPct, platformCoverage, topPainCategories, tag, negThemes, negVolume };
    });
  }, [top10Countries, top20, vocSummary]);

  return (
    <section id="overview" ref={ref} className="viz-section">
      <h2 className="viz-section-title">数据源概览</h2>

      <div style={{
        display: "flex", gap: "var(--space-md)", alignItems: "center", flexWrap: "wrap",
        marginBottom: "var(--space-lg)",
        padding: "var(--space-sm) var(--space-md)",
        background: "var(--color-bg-card)", border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
      }}>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, color: "var(--color-text-secondary)" }}>
          国家
          <select value={filterCountry} onChange={(e) => setFilterCountry(e.target.value)}>
            <option value="all">全部国家 ({allCountries.length})</option>
            {allCountries.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, color: "var(--color-text-secondary)" }}>
          媒体类型
          <select value={filterMediaType} onChange={(e) => setFilterMediaType(e.target.value)}>
            <option value="all">全部类型 ({allMediaTypes.length})</option>
            {allMediaTypes.map((mt) => <option key={mt} value={mt}>{PLATFORM_TYPE_LABEL[mt] || mt}</option>)}
          </select>
        </label>
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--color-text-muted)" }}>
          {matrixData.countryList.length} 国 x {matrixData.mediaTypes.length} 类型
        </span>
      </div>

      <div className="table-wrap" style={{ marginBottom: "var(--space-lg)" }}>
        <table>
          <thead>
            <tr>
              <th style={{ minWidth: 80 }}>国家</th>
              {matrixData.mediaTypes.map((mt) => (
                <th key={mt} style={{ minWidth: 160, textAlign: "center" }}>
                  {PLATFORM_TYPE_LABEL[mt] || mt}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrixData.countryList.map((country) => (
              <tr key={country}>
                <td style={{ fontWeight: 600, fontSize: 13, whiteSpace: "nowrap" }}>{country}</td>
                {matrixData.mediaTypes.map((mt) => {
                  const items = matrixData.matrix[country]?.[mt] || [];
                  return (
                    <td key={mt} style={{ verticalAlign: "top", padding: "8px 10px" }}>
                      {items.length > 0 ? (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {items.map((item) => (
                            <PlatformMiniCard key={item.name} name={item.name} type={item.type} />
                          ))}
                        </div>
                      ) : (
                        <span style={{ color: "var(--color-text-muted)", fontSize: 12 }}>—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <InsightCallout
        title="数据源矩阵解读"
        summary={`当前筛选下共 ${matrixData.countryList.length} 个国家 x ${matrixData.mediaTypes.length} 类媒体类型。`}
        bullets={[
          "单元格内每张小卡片代表一个已覆盖的平台/社区（含 Logo）",
          "空白单元格「—」表示该国该类型暂无平台入口数据",
          "使用筛选器可聚焦特定国家或特定媒体类型",
        ]}
        badge="数据覆盖"
      />

      <div style={{ marginTop: "var(--space-lg)" }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: "var(--space-md)" }}>
          TOP10 国家差异化洞察
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "var(--space-md)" }}>
          {top10Insights.map((item) => (
            <div
              key={item.code}
              className="card"
              style={{ padding: "var(--space-md)", display: "flex", flexDirection: "column", gap: 8 }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: 15 }}>{item.name}</strong>
                <span
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--color-info-bg)",
                    border: "1px solid var(--color-border)",
                    fontWeight: 600,
                  }}
                >
                  {item.tag}
                </span>
              </div>
              <p style={{ fontSize: 13, color: "var(--color-text-secondary)", lineHeight: 1.6, margin: 0 }}>
                {item.insight || "暂无洞察"}
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-sm)", fontSize: 12, marginTop: "auto", paddingTop: 6, borderTop: "1px solid var(--color-border)" }}>
                <span>负面条目 <strong>{item.totalComments}</strong></span>
                <span>高强度 <strong>{item.highIntensityPct > 0 ? `${item.highIntensityPct.toFixed(0)}%` : "—"}</strong></span>
                <span>平台覆盖 <strong>{item.platformCoverage || "—"}</strong></span>
                {item.topPainCategories.length > 0 && (
                  <span>痛点 <strong>{item.topPainCategories.map((p: { label: string; pct: number }) => `${p.label}${p.pct.toFixed(0)}%`).join(" / ")}</strong></span>
                )}
              </div>
              {item.negThemes && (
                <div style={{ fontSize: 12, color: "var(--color-error)", paddingTop: 4, borderTop: "1px dashed var(--color-border)" }}>
                  <span style={{ fontWeight: 600 }}>负面声量: {item.negVolume || "—"}</span>
                  <span style={{ marginLeft: 8, color: "var(--color-text-secondary)" }}>痛点: {item.negThemes}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
});

OverviewSection.displayName = "OverviewSection";
export default OverviewSection;
