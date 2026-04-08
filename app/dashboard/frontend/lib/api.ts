const STATIC_MODE = process.env.NEXT_PUBLIC_STATIC_MODE === "true";
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || "";

const STATIC_FILE_MAP: Record<string, string> = {
  "/api/v1/research/viz-data": "viz_dataset.json",
  "/api/v1/analysis/data": "viz_country_insight.json",
  "/api/v1/opportunity/data": "viz_opportunity.json",
  "/api/v1/opportunity/internal": "viz_opportunity_internal.json",
  "/api/v1/insight/breastpump": "insight_breastpump.json",
  "/api/v1/insight/feedingappliance": "insight_feedingappliance.json",
  "/api/v1/insight/internal/breastpump": "insight_internal_breastpump.json",
  "/api/v1/insight/internal/feedingappliance": "insight_internal_feedingappliance.json",
};

let _cachedVizData: VizDataset | null = null;
let _cachedCountryInsightData: VizDataset | null = null;
let _cachedOpportunityData: VizDataset | null = null;
let _cachedOpportunityInternalData: VizDataset | null = null;

let _vizDataPromise: Promise<VizDataset> | null = null;
let _countryInsightPromise: Promise<VizDataset> | null = null;
let _opportunityPromise: Promise<VizDataset> | null = null;
let _opportunityInternalPromise: Promise<VizDataset> | null = null;

async function fetchJSON<T>(path: string): Promise<T> {
  if (STATIC_MODE) {
    const staticFile = STATIC_FILE_MAP[path];
    if (staticFile) {
      const res = await fetch(`${BASE_PATH}/data/${staticFile}`);
      if (!res.ok) throw new Error(`Static data not found: ${staticFile}`);
      return res.json() as Promise<T>;
    }
    throw new Error(`No static mapping for: ${path}`);
  }
  const base = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  const res = await fetch(`${base}${path}`);
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

async function getVizDataCached(): Promise<VizDataset> {
  if (_cachedVizData) return _cachedVizData;
  if (!_vizDataPromise) {
    _vizDataPromise = fetchJSON<VizDataset>("/api/v1/research/viz-data")
      .then((data) => {
        _cachedVizData = data;
        return data;
      })
      .catch((error) => {
        _vizDataPromise = null;
        throw error;
      });
  }
  return _vizDataPromise;
}

async function getCountryInsightDataCached(): Promise<VizDataset> {
  if (_cachedCountryInsightData) return _cachedCountryInsightData;
  if (!_countryInsightPromise) {
    _countryInsightPromise = fetchJSON<VizDataset>("/api/v1/analysis/data")
      .then((data) => {
        _cachedCountryInsightData = data;
        return data;
      })
      .catch((error) => {
        _countryInsightPromise = null;
        throw error;
      });
  }
  return _countryInsightPromise;
}

async function getOpportunityDataCached(): Promise<VizDataset> {
  if (_cachedOpportunityData) return _cachedOpportunityData;
  if (!_opportunityPromise) {
    _opportunityPromise = fetchJSON<VizDataset>("/api/v1/opportunity/data")
      .then((data) => {
        _cachedOpportunityData = data;
        return data;
      })
      .catch((error) => {
        _opportunityPromise = null;
        throw error;
      });
  }
  return _opportunityPromise;
}

async function getOpportunityInternalDataCached(): Promise<VizDataset> {
  if (_cachedOpportunityInternalData) return _cachedOpportunityInternalData;
  if (!_opportunityInternalPromise) {
    _opportunityInternalPromise = fetchJSON<VizDataset>("/api/v1/opportunity/internal")
      .then((data) => {
        _cachedOpportunityInternalData = data;
        return data;
      })
      .catch((error) => {
        _opportunityInternalPromise = null;
        throw error;
      });
  }
  return _opportunityInternalPromise;
}

export interface Country {
  code: string;
  name_cn: string;
  is_top20: boolean;
  is_top10: boolean;
  sales_amount: number | null;
}

export interface VizDataset {
  meta: {
    generated_at: string;
    source_files?: string[];
    total_countries: number;
    total_product_lines: number;
  };
  overview: { key: string; value: string | number; desc?: string }[];
  countries: Country[];
  personas: Record<string, unknown>[];
  top20: Record<string, unknown>[];
  clusters: Record<string, unknown>[];
  purchasing_power: Record<string, unknown>[];
  trust_sources: Record<string, unknown>[];
  platforms: Record<string, unknown>[];
  keywords: Record<string, unknown>[];
  p1_search?: Record<string, unknown>[];
  segments?: Record<string, unknown>[];
  voc_summary: Record<string, unknown>[];
  voc_persona_summary?: Record<string, unknown>[];
  voc_negative?: Record<string, unknown>[];
}

export interface TableInfo {
  filename: string;
  exists: boolean;
  rows: number;
  size_bytes: number;
  modified_at: string | null;
  dashboards: string[];
}

export interface JsonInfo {
  filename: string;
  exists: boolean;
  size_bytes: number;
  modified_at: string | null;
}

export const API_BASE = STATIC_MODE ? BASE_PATH : (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000");

export const api = {
  health: () => STATIC_MODE
    ? Promise.resolve({ status: "static" })
    : fetchJSON<{ status: string }>("/health"),

  countries: async (params?: { top20?: boolean; top10?: boolean }) => {
    if (STATIC_MODE) {
      const ds = await getVizDataCached();
      let result = ds.countries;
      if (params?.top20) result = result.filter((c) => c.is_top20);
      if (params?.top10) result = result.filter((c) => c.is_top10);
      return result;
    }
    const q = new URLSearchParams();
    if (params?.top20 !== undefined) q.set("top20", String(params.top20));
    if (params?.top10 !== undefined) q.set("top10", String(params.top10));
    const qs = q.toString();
    return fetchJSON<Country[]>(`/api/v1/countries/${qs ? `?${qs}` : ""}`);
  },

  countryDetail: async (code: string) => {
    if (STATIC_MODE) {
      const ds = await getVizDataCached();
      const codeUpper = code.toUpperCase();
      const country = ds.countries.find((c) => c.code === codeUpper);
      if (!country) throw new Error(`Country ${code} not found`);
      return {
        country,
        personas: ds.personas.filter((p) => (p as Record<string, unknown>).country_code === codeUpper),
        purchasing_power: ds.purchasing_power.filter((p) => (p as Record<string, unknown>).country_code === codeUpper),
        trust_sources: ds.trust_sources.filter((t) => (t as Record<string, unknown>).country_code === codeUpper),
        platforms: ds.platforms.filter((p) => (p as Record<string, unknown>).country_code === codeUpper),
        keywords: ds.keywords.filter((k) => (k as Record<string, unknown>).country_code === codeUpper),
        voc_summary: ds.voc_summary.filter((v) => (v as Record<string, unknown>).country_code === codeUpper),
      };
    }
    return fetchJSON<Record<string, unknown>>(`/api/v1/countries/${code}`);
  },

  vizData: () => fetchJSON<VizDataset>("/api/v1/research/viz-data"),
  countryInsightData: () => getCountryInsightDataCached(),
  opportunityData: () => getOpportunityDataCached(),
  opportunityInternalData: () => getOpportunityInternalDataCached(),

  reloadDatasets: () => STATIC_MODE
    ? Promise.resolve({ status: "static mode - no reload" })
    : fetchJSON<{ status: string }>("/api/v1/research/reload"),

  overview: async () => {
    if (STATIC_MODE) {
      const ds = await getVizDataCached();
      return ds.overview;
    }
    return fetchJSON<{ key: string; value: string | number }[]>("/api/v1/research/overview");
  },

  meta: async () => {
    if (STATIC_MODE) {
      const ds = await getVizDataCached();
      return ds.meta as Record<string, unknown>;
    }
    return fetchJSON<Record<string, unknown>>("/api/v1/research/meta");
  },

  clusters: async () => {
    if (STATIC_MODE) {
      const ds = await getVizDataCached();
      return ds.clusters;
    }
    return fetchJSON<Record<string, unknown>[]>("/api/v1/research/clusters");
  },

  top20: async () => {
    if (STATIC_MODE) {
      const ds = await getVizDataCached();
      return ds.top20;
    }
    return fetchJSON<Record<string, unknown>[]>("/api/v1/research/top20");
  },

  adminStatus: () => STATIC_MODE
    ? Promise.resolve({ tables: [] as TableInfo[], json_outputs: [] as JsonInfo[] })
    : fetchJSON<{ tables: TableInfo[]; json_outputs: JsonInfo[] }>("/api/v1/admin/status"),

  insightData: (productLine: string, options?: { internal?: boolean }) =>
    fetchJSON<Record<string, unknown>>(
      options?.internal
        ? `/api/v1/insight/internal/${productLine}`
        : `/api/v1/insight/${productLine}`
    ),
};
