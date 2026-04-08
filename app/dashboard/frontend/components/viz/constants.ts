export const CHART_COLORS = [
  "var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)",
  "var(--chart-5)", "var(--chart-6)", "var(--chart-7)", "var(--chart-8)",
  "var(--chart-9)", "var(--chart-10)",
];

export const CHART_COLORS_RAW = [
  "#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
  "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
];

export const COUNTRY_INSIGHT_SECTIONS = [
  { id: "overview", label: "数据源概览" },
  { id: "countries", label: "国家全景" },
  { id: "top20", label: "TOP20 深挖" },
  { id: "clusters", label: "区域聚类" },
  { id: "personas", label: "用户画像" },
  { id: "segments", label: "客群矩阵" },
  { id: "purchasing", label: "购买力分层" },
  { id: "products", label: "品线洞察" },
] as const;

export const OPPORTUNITY_SECTIONS = [
  { id: "opp-summary", label: "机会点摘要",  group: "conclusion" },
  { id: "platforms",   label: "渠道覆盖",    group: "channel"    },
  { id: "trust",       label: "信源质量",    group: "channel"    },
  { id: "vocsummary",  label: "声量全景",    group: "pain"       },
  { id: "vocnegative", label: "痛点深挖",    group: "pain"       },
  { id: "competitor",  label: "竞品图谱",    group: "competitor" },
  { id: "timeline",    label: "趋势追踪",    group: "trend"      },
  { id: "p1search",    label: "执行作业单",  group: "action"     },
] as const;

export const OPPORTUNITY_GROUPS = [
  { key: "conclusion", label: "结论摘要" },
  { key: "channel",    label: "WHERE 渠道" },
  { key: "pain",       label: "WHAT 痛点" },
  { key: "competitor", label: "WHO 竞品" },
  { key: "trend",      label: "WHEN 趋势" },
  { key: "action",     label: "HOW 执行" },
] as const;

export const SECTIONS = [...COUNTRY_INSIGHT_SECTIONS, ...OPPORTUNITY_SECTIONS] as const;

export type CountryInsightSectionId = (typeof COUNTRY_INSIGHT_SECTIONS)[number]["id"];
export type OpportunitySectionId = (typeof OPPORTUNITY_SECTIONS)[number]["id"];
export type SectionId = CountryInsightSectionId | OpportunitySectionId;
