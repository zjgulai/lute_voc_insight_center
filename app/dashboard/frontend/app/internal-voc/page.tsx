"use client";

import { useEffect, useState, useRef, useMemo, Suspense, type ForwardRefExoticComponent, type RefAttributes } from "react";
import { useSearchParams } from "next/navigation";
import { api, type VizDataset } from "../../lib/api";
import { OPPORTUNITY_SECTIONS, OPPORTUNITY_GROUPS } from "../../components/viz/constants";
import {
  OpportunitySummarySection,
  PlatformsSection,
  TrustSourcesSection,
  VOCSummarySection,
  NegativeVOCSection,
  CompetitorSection,
  TimelineTrendSection,
  P1SearchSection,
} from "../../components/viz";

type R = Record<string, unknown>;
function s(v: unknown): string { return String(v ?? ""); }

type SectionProps = { data: VizDataset; filterCountry?: string; filterProductLine?: string; filterBrand?: string };
type SectionComponent = ForwardRefExoticComponent<SectionProps & RefAttributes<HTMLElement>>;

const SECTION_MAP: Record<string, SectionComponent> = {
  "opp-summary": OpportunitySummarySection as unknown as SectionComponent,
  platforms: PlatformsSection as unknown as SectionComponent,
  trust: TrustSourcesSection as unknown as SectionComponent,
  vocsummary: VOCSummarySection as unknown as SectionComponent,
  vocnegative: NegativeVOCSection as unknown as SectionComponent,
  competitor: CompetitorSection as unknown as SectionComponent,
  timeline: TimelineTrendSection as unknown as SectionComponent,
  p1search: P1SearchSection as unknown as SectionComponent,
};

const SECTIONS_WITH_FILTER = new Set(["opp-summary", "vocsummary", "vocnegative", "competitor", "timeline"]);

const GROUP_LAYER_LABELS: Record<string, { subtitle: string }> = {
  conclusion: { subtitle: "内部 Momcozy VOC 的核心结论与优先级判断" },
  channel: { subtitle: "内部反馈主要来源平台与信号强度" },
  pain: { subtitle: "内部高频痛点与原文明细" },
  competitor: { subtitle: "内部反馈关联到的品牌与痛点映射" },
  trend: { subtitle: "内部痛点随时间的演变趋势" },
  action: { subtitle: "用于内部复盘与跟进的采集作业单" },
};

const ENABLED_INTERNAL_SECTIONS = new Set(["opp-summary", "vocsummary", "vocnegative", "competitor", "timeline"]);

export default function InternalVOCPageWrapper() {
  return (
    <Suspense fallback={<div className="loading-text">加载中...</div>}>
      <InternalVOCPage />
    </Suspense>
  );
}

function InternalVOCPage() {
  const [data, setData] = useState<VizDataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>(OPPORTUNITY_SECTIONS[0].id);
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});

  const searchParams = useSearchParams();
  const [globalCountry, setGlobalCountry] = useState(searchParams?.get("country") || "all");
  const [globalProductLine, setGlobalProductLine] = useState(searchParams?.get("line") || "all");
  const [globalBrand, setGlobalBrand] = useState(searchParams?.get("brand") || "all");

  useEffect(() => {
    api.opportunityInternalData().then(setData).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        }
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );
    Object.values(sectionRefs.current).forEach((el) => {
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [data]);

  const vocNeg = ((data as unknown as R)?.voc_negative ?? []) as R[];

  const countryOptions = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.country)).filter(Boolean));
    return Array.from(set).sort();
  }, [vocNeg]);

  const lineOptions = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.product_line)).filter(Boolean));
    return Array.from(set).sort();
  }, [vocNeg]);

  const brandOptions = useMemo(() => {
    const set = new Set(vocNeg.map((r) => s(r.competitor_brand)).filter(Boolean));
    return Array.from(set).sort();
  }, [vocNeg]);

  if (error) return <div className="alert-error">{error}</div>;
  if (!data) return <div className="loading-text">加载数据集中...</div>;

  const sectionsByGroup = OPPORTUNITY_GROUPS.map((g) => ({
    ...g,
    sections: OPPORTUNITY_SECTIONS.filter((s) => s.group === g.key && ENABLED_INTERNAL_SECTIONS.has(s.id)),
  }));

  return (
    <div className="viz-layout">
      <aside className="viz-sidebar">
        <div className="opp-global-filter" style={{ flexDirection: "column", alignItems: "stretch", padding: "var(--space-sm) var(--space-md)", marginBottom: "var(--space-md)" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)" }}>
            国家
            <select value={globalCountry} onChange={(e) => setGlobalCountry(e.target.value)} style={{ flex: 1 }}>
              <option value="all">全部国家</option>
              {countryOptions.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", marginTop: 6 }}>
            品线
            <select value={globalProductLine} onChange={(e) => setGlobalProductLine(e.target.value)} style={{ flex: 1 }}>
              <option value="all">全部品线</option>
              {lineOptions.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", marginTop: 6 }}>
            品牌
            <select value={globalBrand} onChange={(e) => setGlobalBrand(e.target.value)} style={{ flex: 1 }}>
              <option value="all">全部品牌</option>
              {brandOptions.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </label>
        </div>
        <nav aria-label="内部 VOC 看板导航">
          {sectionsByGroup.map((g) => (
            <div key={g.key} style={{ marginBottom: "var(--space-md)" }}>
              <div style={{
                fontSize: 10,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "var(--color-text-muted)",
                padding: "4px 14px",
              }}>
                {g.label}
              </div>
              {g.sections.map((sec) => (
                <a
                  key={sec.id}
                  href={`#${sec.id}`}
                  className="viz-sidebar-link"
                  data-active={activeSection === sec.id}
                  onClick={(e) => {
                    e.preventDefault();
                    sectionRefs.current[sec.id]?.scrollIntoView({ behavior: "smooth" });
                  }}
                  style={{ paddingLeft: 22 }}
                >
                  {sec.label}
                </a>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <div className="viz-main">
        <div className="card" style={{ marginBottom: "var(--space-md)", padding: "var(--space-md) var(--space-lg)" }}>
          <div className="card-title" style={{ marginBottom: 4 }}>内部 Momcozy VOC 看板</div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
            主 KPI 为证据条数；frequency 仅作为内部辅助信息，不作为主展示口径。
          </div>
        </div>
        {sectionsByGroup.map((g) => (
          <div key={g.key}>
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-md)",
              padding: "var(--space-md) 0",
              marginBottom: "var(--space-sm)",
              borderBottom: "2px solid var(--color-border)",
            }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--color-primary)" }}>
                  {g.label}
                </div>
                <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
                  {GROUP_LAYER_LABELS[g.key]?.subtitle || ""}
                </div>
              </div>
            </div>

            {g.sections.map((sec) => {
              const Component = SECTION_MAP[sec.id];
              if (!Component) return null;
              const extraProps = SECTIONS_WITH_FILTER.has(sec.id)
                ? { filterCountry: globalCountry, filterProductLine: globalProductLine, filterBrand: globalBrand }
                : {};
              return (
                <Component
                  key={sec.id}
                  data={data}
                  {...extraProps}
                  ref={(el: HTMLElement | null) => {
                    sectionRefs.current[sec.id] = el;
                  }}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
