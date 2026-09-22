import { useRef, useState } from "react";

import { getSeverity } from "../api";
import type { LangCode, SeverityResponse } from "../types";
import AudioPlayer from "./AudioPlayer";

interface Props {
  lang: LangCode;
  lat?: number;
  lon?: number;
}

const SCAN_MS = 5000;
const FRAME_INTERVAL_MS = 500;
const TOTAL_FRAMES = SCAN_MS / FRAME_INTERVAL_MS;

const LEVEL_LABEL: Record<string, string> = {
  low: "Low (<15%)",
  moderate: "Moderate (15-40%)",
  high: "High (>40%)",
};

function barColor(pct: number): string {
  if (pct < 15) return "bg-green-600";
  if (pct <= 40) return "bg-yellow-500";
  return "bg-red-600";
}

export default function SeverityScan({ lang, lat, lon }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scanning, setScanning] = useState(false);
  const [framesCaptured, setFramesCaptured] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SeverityResponse | null>(null);

  function captureFrame(): Promise<Blob | null> {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return Promise.resolve(null);
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return Promise.resolve(null);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve) => canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.85));
  }

  async function startScan() {
    setError(null);
    setResult(null);
    setFramesCaptured(0);

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    } catch {
      setError("Could not access the camera. Check camera permission and try again.");
      return;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    }
    setScanning(true);

    const frames: Blob[] = [];
    for (let i = 0; i < TOTAL_FRAMES; i++) {
      await new Promise((r) => setTimeout(r, FRAME_INTERVAL_MS));
      const blob = await captureFrame();
      if (blob) frames.push(blob);
      setFramesCaptured(i + 1);
    }

    stream.getTracks().forEach((t) => t.stop());
    setScanning(false);

    if (frames.length === 0) {
      setError("No frames captured. Please try scanning again.");
      return;
    }

    setLoading(true);
    try {
      const res = await getSeverity(frames, lang, { lat, lon });
      setResult(res);
    } catch {
      setError("Could not reach the severity service. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const progressPct = Math.round((framesCaptured / TOTAL_FRAMES) * 100);

  return (
    <div className="rounded-2xl bg-white shadow p-5 flex flex-col gap-4 border border-green-100">
      <p className="text-xl font-bold text-green-900">Field severity scan</p>

      <video ref={videoRef} className={scanning ? "w-full rounded-xl" : "hidden"} muted playsInline />
      <canvas ref={canvasRef} className="hidden" />

      {!scanning && (
        <button
          onClick={startScan}
          disabled={loading}
          className="rounded-full bg-green-700 text-white px-6 py-3 text-lg font-semibold shadow active:scale-95 disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "🎥 Scan field (5s)"}
        </button>
      )}

      {scanning && (
        <div className="flex flex-col items-center gap-2">
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="30" fill="none" stroke="#e5e7eb" strokeWidth="8" />
            <circle
              cx="36"
              cy="36"
              r="30"
              fill="none"
              stroke="#15803d"
              strokeWidth="8"
              strokeDasharray={`${(progressPct / 100) * 188.5} 188.5`}
              strokeLinecap="round"
              transform="rotate(-90 36 36)"
            />
          </svg>
          <p className="text-sm text-gray-600">
            Capturing… {framesCaptured}/{TOTAL_FRAMES}
          </p>
        </div>
      )}

      {error && <p className="text-center text-red-600 bg-red-50 rounded-lg py-2 px-3">{error}</p>}

      {result && !loading && (
        <>
          {result.llm_fallback && (
            <div className="rounded-lg bg-yellow-100 text-yellow-900 text-sm px-3 py-2 font-medium">
              AI model unavailable — showing standard advice
            </div>
          )}

          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-sm text-gray-600">
              <span>{result.severity.crop !== "Unknown" ? result.severity.crop : "Field"} — {result.severity.disease}</span>
              <span className="font-semibold">{result.severity.severity_pct}%</span>
            </div>
            <div className="w-full h-4 rounded-full bg-gray-100 overflow-hidden">
              <div
                className={`h-full ${barColor(result.severity.severity_pct)}`}
                style={{ width: `${Math.min(100, result.severity.severity_pct)}%` }}
              />
            </div>
            <p className="text-center text-sm font-semibold text-gray-700">
              {LEVEL_LABEL[result.severity.severity_level]}
            </p>
          </div>

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
