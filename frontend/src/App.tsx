import { useState } from "react";

import { diagnose } from "./api";
import AskBar from "./components/AskBar";
import AudioPlayer from "./components/AudioPlayer";
import Capture from "./components/Capture";
import DiagnosisCard from "./components/DiagnosisCard";
import DosageForm from "./components/DosageForm";
import GeoChip from "./components/GeoChip";
import LanguagePills from "./components/LanguagePills";
import OfflineBadge from "./components/OfflineBadge";
import ScanHistory, { type HistoryEntry } from "./components/ScanHistory";
import SeverityScan from "./components/SeverityScan";
import StageLoader from "./components/StageLoader";
import Toast from "./components/Toast";
import { UI_STRINGS } from "./i18n/labels";
import type { AskContext, DiagnoseResponse, LangCode } from "./types";

const MAX_HISTORY = 5;

export default function App() {
  const [lang, setLang] = useState<LangCode>("kn");
  const [coords, setCoords] = useState<{ lat?: number; lon?: number }>({});
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnoseResponse | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  async function handleCapture(file: File) {
    setLoading(true);
    setToast(null);
    setResult(null);
    try {
      const res = await diagnose(file, lang, { lat: coords.lat, lon: coords.lon });
      setResult(res);
      setHistory((h) =>
        [
          {
            crop: res.diagnosis.crop,
            disease: res.diagnosis.disease,
            confidencePct: Math.round(res.diagnosis.confidence * 100),
            time: new Date().toLocaleTimeString(),
          },
          ...h,
        ].slice(0, MAX_HISTORY),
      );
    } catch {
      setToast("Could not reach the diagnosis service. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const askContext: AskContext = result
    ? {
        crop: result.diagnosis.crop,
        disease: result.diagnosis.disease,
        severity_or_confidence: `${Math.round(result.diagnosis.confidence * 100)} percent confidence`,
        treatment_summary: result.plan_text.slice(0, 300),
      }
    : {};

  return (
    <div className="min-h-screen flex flex-col items-center bg-gray-50">
      <div className="w-full max-w-md px-4 py-8 flex flex-col gap-6">
        <OfflineBadge />
        <h1 className="text-3xl font-extrabold text-center text-green-800">
          {UI_STRINGS[lang].title}
        </h1>

        <LanguagePills value={lang} onChange={setLang} />
        <GeoChip onLocated={(lat, lon) => setCoords({ lat, lon })} />

        <Capture label={UI_STRINGS[lang].scanLeaf} onCapture={handleCapture} />

        {loading && <StageLoader />}

        {result && !loading && (
          <>
            <DiagnosisCard result={result} />
            <AudioPlayer
              audioUrl={result.audio_url}
              ttsFallback={result.tts_fallback}
              fallbackText={result.plan_text}
            />
            {result.diagnosis.disease_key && (
              <DosageForm diseaseKey={result.diagnosis.disease_key} lang={lang} />
            )}
            <AskBar lang={lang} context={askContext} />
          </>
        )}

        <SeverityScan lang={lang} lat={coords.lat} lon={coords.lon} />

        <ScanHistory entries={history} />
      </div>

      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}
    </div>
  );
}
