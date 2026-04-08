const SEGMENT_FALLBACK_NAME: Record<string, string> = {
  SEG01: "产后建奶新手妈妈",
  SEG02: "精细喂养效率型妈妈",
  SEG03: "高频泵奶复购家庭",
  SEG04: "孕产护理妈妈",
  SEG05: "清洁护理妈妈",
  SEG06: "综合护理家庭",
  SEG07: "智能育儿家庭",
  SEG08: "家居布品家庭",
  SEG99: "综合育儿用户",
};

export function extractSegmentCode(value: string): string | null {
  const m = String(value ?? "").toUpperCase().match(/SEG\d{2}/);
  return m ? m[0] : null;
}

export function getSegmentDisplayName(code: string, segmentName?: string): string {
  const name = String(segmentName ?? "").trim();
  if (name) return name;
  const normalizedCode = extractSegmentCode(code);
  if (!normalizedCode) return String(code ?? "");
  return SEGMENT_FALLBACK_NAME[normalizedCode] ?? normalizedCode;
}
