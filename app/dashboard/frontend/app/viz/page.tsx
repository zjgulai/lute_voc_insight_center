"use client";

import { useEffect, useState, useRef, type ForwardRefExoticComponent, type RefAttributes } from "react";
import { api, type VizDataset } from "../../lib/api";
import { COUNTRY_INSIGHT_SECTIONS } from "../../components/viz/constants";
import {
  OverviewSection,
  CountriesSection,
  Top20Section,
  ClustersSection,
  PersonasSection,
  PurchasingSection,
  ProductsSection,
  SegmentsSection,
} from "../../components/viz";

type SectionComponent = ForwardRefExoticComponent<{ data: VizDataset } & RefAttributes<HTMLElement>>;

const SECTION_MAP: Record<string, SectionComponent> = {
  overview: OverviewSection,
  countries: CountriesSection,
  top20: Top20Section,
  clusters: ClustersSection,
  personas: PersonasSection,
  segments: SegmentsSection,
  purchasing: PurchasingSection,
  products: ProductsSection,
};

export default function CountryInsightPage() {
  const [data, setData] = useState<VizDataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>(COUNTRY_INSIGHT_SECTIONS[0].id);
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});

  useEffect(() => {
    api.countryInsightData().then(setData).catch((e) => setError(e.message));
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

  if (error) return <div className="alert-error">{error}</div>;
  if (!data) return <div className="loading-text">加载数据集中...</div>;

  return (
    <div className="viz-layout">
      <aside className="viz-sidebar">
        <nav aria-label="国家洞察导航">
          {COUNTRY_INSIGHT_SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="viz-sidebar-link"
              data-active={activeSection === s.id}
              onClick={(e) => {
                e.preventDefault();
                sectionRefs.current[s.id]?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              {s.label}
            </a>
          ))}
        </nav>
      </aside>

      <div className="viz-main">
        {COUNTRY_INSIGHT_SECTIONS.map((s) => {
          const Component = SECTION_MAP[s.id];
          if (!Component) return null;
          return (
            <Component
              key={s.id}
              data={data}
              ref={(el: HTMLElement | null) => {
                sectionRefs.current[s.id] = el;
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
