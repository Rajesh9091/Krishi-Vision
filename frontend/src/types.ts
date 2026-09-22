// Mirrors backend pydantic response shapes exactly (snake_case).

export type LangCode = "kn" | "hi" | "te" | "ta" | "en";

export interface Zone {
  id: string;
  name: string;
  state: string;
  soil?: string;
  climate?: string;
  season_note?: string;
}

export interface Scheme {
  id: string;
  name: string;
  summary: string;
}

export interface ContextResponse {
  zone: Zone;
  schemes: Scheme[];
}

export interface TopLabel {
  label: string;
  score: number;
}

export interface Diagnosis {
  crop: string;
  disease: string;
  confidence: number;
  uncertain?: boolean;
  top3?: TopLabel[];
  disease_key?: string | null;
}

export interface TimingsMs {
  vision: number;
  llm: number;
  tts: number;
  total: number;
}

export interface DiagnoseResponse {
  diagnosis: Diagnosis;
  plan_text: string;
  plan_text_lang: LangCode;
  llm_fallback?: boolean;
  audio_url: string | null;
  tts_fallback?: "browser" | null;
  zone: Zone;
  schemes: Scheme[];
  timings_ms: TimingsMs;
}

export type AreaUnit = "acre" | "hectare" | "gunta";
export type TreatmentPref = "organic" | "chemical" | "any";

export interface DosageNumbers {
  crop: string;
  disease: string;
  treatment_name: string;
  treatment_type: "organic" | "chemical";
  area_value: number;
  area_unit: AreaUnit;
  area_acres: number;
  water_litres: number;
  product_amount: number;
  product_unit: string;
  per_tank_amount: number;
  tank_fills: number;
  interval_days: number;
  max_applications: number;
  safety: string;
}

export interface DosageTimingsMs {
  llm: number;
  tts: number;
  total: number;
}

export interface DosageResponse {
  numbers: DosageNumbers;
  plan_text: string;
  plan_text_lang: LangCode;
  llm_fallback?: boolean;
  audio_url: string | null;
  tts_fallback?: "browser" | null;
  timings_ms: DosageTimingsMs;
}

export type SeverityLevel = "low" | "moderate" | "high";

export interface SeverityFrameStat {
  boxes: number;
  infected: number;
}

export interface SeverityInfo {
  severity_pct: number;
  severity_level: SeverityLevel;
  crop: string;
  disease: string;
  disease_key: string | null;
  total_boxes: number;
  infected_boxes: number;
  per_frame: SeverityFrameStat[];
}

export interface SeverityTimingsMs {
  vision: number;
  llm: number;
  tts: number;
  total: number;
}

export interface SeverityResponse {
  severity: SeverityInfo;
  plan_text: string;
  plan_text_lang: LangCode;
  llm_fallback?: boolean;
  audio_url: string | null;
  tts_fallback?: "browser" | null;
  zone: Zone;
  timings_ms: SeverityTimingsMs;
}

export interface AskContext {
  crop?: string;
  disease?: string;
  severity_or_confidence?: string;
  treatment_summary?: string;
  dosage_summary?: string;
}

export interface AskTurn {
  question: string;
  answer: string;
}

export interface AskTimingsMs {
  asr: number;
  llm: number;
  tts: number;
  total: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  asr_error?: string | null;
  llm_fallback?: boolean;
  audio_url: string | null;
  tts_fallback?: "browser" | null;
  timings_ms: AskTimingsMs;
}
