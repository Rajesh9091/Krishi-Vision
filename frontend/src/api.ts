import type {
  AreaUnit,
  AskContext,
  AskResponse,
  AskTurn,
  ContextResponse,
  DiagnoseResponse,
  DosageResponse,
  LangCode,
  SeverityResponse,
  TreatmentPref,
} from "./types";

const BASE = "/api";

export async function getContext(lat?: number, lon?: number, crop?: string): Promise<ContextResponse> {
  const params = new URLSearchParams();
  if (lat !== undefined) params.set("lat", String(lat));
  if (lon !== undefined) params.set("lon", String(lon));
  if (crop) params.set("crop", crop);

  const res = await fetch(`${BASE}/context?${params.toString()}`);
  if (!res.ok) throw new Error(`context failed: ${res.status}`);
  return res.json();
}

export async function diagnose(
  image: File,
  lang: LangCode,
  opts: { lat?: number; lon?: number; cropHint?: string; stub?: boolean } = {},
): Promise<DiagnoseResponse> {
  const form = new FormData();
  form.set("image", image);
  form.set("lang", lang);
  if (opts.lat !== undefined) form.set("lat", String(opts.lat));
  if (opts.lon !== undefined) form.set("lon", String(opts.lon));
  if (opts.cropHint) form.set("crop_hint", opts.cropHint);

  const query = opts.stub ? "?stub=true" : "";
  const res = await fetch(`${BASE}/diagnose${query}`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`diagnose failed: ${res.status}`);
  return res.json();
}

export async function getDosage(
  diseaseKey: string,
  areaValue: number,
  areaUnit: AreaUnit,
  lang: LangCode,
  treatmentPref: TreatmentPref,
): Promise<DosageResponse> {
  const res = await fetch(`${BASE}/dosage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      disease_key: diseaseKey,
      area_value: areaValue,
      area_unit: areaUnit,
      lang,
      treatment_pref: treatmentPref,
    }),
  });
  if (!res.ok) throw new Error(`dosage failed: ${res.status}`);
  return res.json();
}

export async function getSeverity(
  frames: Blob[],
  lang: LangCode,
  opts: { lat?: number; lon?: number } = {},
): Promise<SeverityResponse> {
  const form = new FormData();
  frames.forEach((frame, i) => form.append("frames", frame, `frame_${i}.jpg`));
  form.set("lang", lang);
  if (opts.lat !== undefined) form.set("lat", String(opts.lat));
  if (opts.lon !== undefined) form.set("lon", String(opts.lon));

  const res = await fetch(`${BASE}/severity`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`severity failed: ${res.status}`);
  return res.json();
}

export async function ask(
  input: { audio?: Blob; text?: string },
  lang: LangCode,
  context: AskContext,
  history: AskTurn[],
): Promise<AskResponse> {
  const form = new FormData();
  if (input.audio) form.set("audio", input.audio, "question.webm");
  if (input.text) form.set("text", input.text);
  form.set("lang", lang);
  form.set("context", JSON.stringify(context));
  form.set("history", JSON.stringify(history));

  const res = await fetch(`${BASE}/ask`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`ask failed: ${res.status}`);
  return res.json();
}
