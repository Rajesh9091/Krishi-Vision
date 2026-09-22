import { useState } from "react";

import { getDosage } from "../api";
import type { AreaUnit, DosageResponse, LangCode, TreatmentPref } from "../types";
import AudioPlayer from "./AudioPlayer";

interface Props {
  diseaseKey: string;
  lang: LangCode;
}

const AREA_UNITS: { value: AreaUnit; label: string }[] = [
  { value: "acre", label: "Acre" },
  { value: "hectare", label: "Hectare" },
  { value: "gunta", label: "Gunta" },
];

const TREATMENT_PREFS: { value: TreatmentPref; label: string }[] = [
  { value: "organic", label: "Organic" },
  { value: "chemical", label: "Chemical" },
  { value: "any", label: "Any" },
];

export default function DosageForm({ diseaseKey, lang }: Props) {
  const [areaValue, setAreaValue] = useState("1");
  const [areaUnit, setAreaUnit] = useState<AreaUnit>("acre");
  const [treatmentPref, setTreatmentPref] = useState<TreatmentPref>("organic");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DosageResponse | null>(null);

  async function handleCalculate() {
    const parsed = parseFloat(areaValue);
    if (Number.isNaN(parsed) || parsed <= 0) {
      setError("Enter a valid field size.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await getDosage(diseaseKey, parsed, areaUnit, lang, treatmentPref);
      setResult(res);
    } catch {
      setError("Could not calculate dosage. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl bg-white shadow p-5 flex flex-col gap-4 border border-green-100">
      <p className="text-xl font-bold text-green-900">Dosage calculator</p>

      <div className="flex gap-2 items-center">
        <input
          type="number"
          min="0"
          step="0.1"
          value={areaValue}
          onChange={(e) => setAreaValue(e.target.value)}
          className="w-24 rounded-lg border px-3 py-2 text-lg"
        />
        <div className="flex gap-1">
          {AREA_UNITS.map((u) => (
            <button
              key={u.value}
              onClick={() => setAreaUnit(u.value)}
              className={`rounded-full px-3 py-2 text-sm font-medium ${
                areaUnit === u.value ? "bg-green-700 text-white" : "bg-gray-100 text-gray-700"
              }`}
            >
              {u.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-1">
        {TREATMENT_PREFS.map((p) => (
          <button
            key={p.value}
            onClick={() => setTreatmentPref(p.value)}
            className={`flex-1 rounded-full px-3 py-2 text-sm font-medium ${
              treatmentPref === p.value ? "bg-green-700 text-white" : "bg-gray-100 text-gray-700"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <button
        onClick={handleCalculate}
        disabled={loading}
        className="rounded-full bg-green-700 text-white px-6 py-3 text-lg font-semibold shadow active:scale-95 disabled:opacity-50"
      >
        {loading ? "Calculating…" : "Calculate dosage"}
      </button>

      {error && <p className="text-center text-red-600 bg-red-50 rounded-lg py-2 px-3">{error}</p>}

      {result && !loading && (
        <>
          {result.llm_fallback && (
            <div className="rounded-lg bg-yellow-100 text-yellow-900 text-sm px-3 py-2 font-medium">
              AI model unavailable — showing standard advice
            </div>
          )}

          <table className="w-full text-left text-base">
            <tbody>
              <tr className="border-b">
                <td className="py-1 text-gray-500">Treatment</td>
                <td className="py-1 font-semibold">
                  {result.numbers.treatment_name} ({result.numbers.treatment_type})
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-1 text-gray-500">Total water</td>
                <td className="py-1 font-semibold">{result.numbers.water_litres} L</td>
              </tr>
              <tr className="border-b">
                <td className="py-1 text-gray-500">Total product</td>
                <td className="py-1 font-semibold">
                  {result.numbers.product_amount} {result.numbers.product_unit}
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-1 text-gray-500">Per 15 L tank</td>
                <td className="py-1 font-semibold">
                  {result.numbers.per_tank_amount} {result.numbers.product_unit}
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-1 text-gray-500">Tank fills</td>
                <td className="py-1 font-semibold">{result.numbers.tank_fills}</td>
              </tr>
              <tr>
                <td className="py-1 text-gray-500">Spray interval</td>
                <td className="py-1 font-semibold">
                  Every {result.numbers.interval_days} days, max {result.numbers.max_applications} times
                </td>
              </tr>
            </tbody>
          </table>

          <p className="text-sm text-gray-600">{result.numbers.safety}</p>
          <p className="text-lg leading-relaxed text-gray-900 whitespace-pre-line">{result.plan_text}</p>

          <AudioPlayer
            audioUrl={result.audio_url}
            ttsFallback={result.tts_fallback}
            fallbackText={result.plan_text}
          />
        </>
      )}
    </div>
  );
}
