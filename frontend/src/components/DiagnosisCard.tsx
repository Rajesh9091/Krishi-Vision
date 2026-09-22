import type { DiagnoseResponse } from "../types";

interface Props {
  result: DiagnoseResponse;
}

export default function DiagnosisCard({ result }: Props) {
  const { diagnosis, plan_text, zone, schemes, timings_ms, llm_fallback } = result;
  const confidencePct = Math.round(diagnosis.confidence * 100);

  return (
    <div className="rounded-2xl bg-white shadow p-5 flex flex-col gap-4 border border-green-100">
      {llm_fallback && (
        <div className="rounded-lg bg-yellow-100 text-yellow-900 text-sm px-3 py-2 font-medium">
          AI model unavailable — showing standard advice
        </div>
      )}

      <div>
        <p className="text-2xl font-extrabold text-green-900">
          {diagnosis.crop} · {diagnosis.disease}
        </p>
        <div className="mt-2 h-3 w-full rounded-full bg-gray-200 overflow-hidden">
          <div
            className={`h-3 rounded-full ${confidencePct < 45 ? "bg-yellow-500" : "bg-green-600"}`}
            style={{ width: `${confidencePct}%` }}
          />
        </div>
        <p className="text-sm text-gray-500 mt-1">Confidence: {confidencePct}%</p>
      </div>

      <p className="text-xl leading-relaxed text-gray-900 whitespace-pre-line">{plan_text}</p>

      {schemes.length > 0 && (
        <div className="rounded-lg bg-blue-50 text-blue-900 text-base px-3 py-2">
          🏛 {schemes[0].name} — {schemes[0].summary}
        </div>
      )}

      <p className="text-xs text-gray-400">
        {zone.name}, {zone.state} · Vision {(timings_ms.vision / 1000).toFixed(1)}s · LLM{" "}
        {(timings_ms.llm / 1000).toFixed(1)}s · TTS {(timings_ms.tts / 1000).toFixed(1)}s · on-device
      </p>
    </div>
  );
}
