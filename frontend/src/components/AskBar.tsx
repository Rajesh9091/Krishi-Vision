import { useRef, useState } from "react";

import { ask } from "../api";
import type { AskContext, AskTurn, LangCode } from "../types";
import AudioPlayer from "./AudioPlayer";

interface Props {
  lang: LangCode;
  context: AskContext;
}

export default function AskBar({ lang, context }: Props) {
  const [recording, setRecording] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [turns, setTurns] = useState<AskTurn[]>([]);
  const [lastFallback, setLastFallback] = useState(false);
  const [lastAudio, setLastAudio] = useState<{ url: string | null; fallback: "browser" | null; text: string } | null>(
    null,
  );

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function submit(input: { audio?: Blob; text?: string }) {
    setError(null);
    setLoading(true);
    try {
      const res = await ask(input, lang, context, turns);
      if (res.asr_error) {
        setError("Could not hear that. Please try again or type your question.");
        return;
      }
      setTurns((t) => [...t, { question: res.question, answer: res.answer }]);
      setLastFallback(Boolean(res.llm_fallback));
      setLastAudio({ url: res.audio_url, fallback: res.tts_fallback ?? null, text: res.answer });
      setTextInput("");
    } catch {
      setError("Could not reach the assistant. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        submit({ audio: blob });
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch {
      setError("Could not access the microphone. Check permission and try again, or type below.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  function submitText() {
    if (!textInput.trim()) return;
    submit({ text: textInput.trim() });
  }

  return (
    <div className="rounded-2xl bg-white shadow p-5 flex flex-col gap-4 border border-green-100">
      <p className="text-xl font-bold text-green-900">Ask a follow-up question</p>

      <div className="flex gap-2 items-center">
        <button
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onTouchStart={startRecording}
          onTouchEnd={stopRecording}
          disabled={loading}
          className={`rounded-full px-6 py-4 text-lg font-semibold shadow active:scale-95 disabled:opacity-50 ${
            recording ? "bg-red-600 text-white" : "bg-green-700 text-white"
          }`}
        >
          {recording ? "🔴 Recording… release to send" : "🎙 Hold to ask"}
        </button>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submitText()}
          placeholder="Or type your question…"
          className="flex-1 rounded-lg border px-3 py-2 text-base"
        />
        <button
          onClick={submitText}
          disabled={loading || !textInput.trim()}
          className="rounded-lg bg-green-700 text-white px-4 py-2 font-semibold disabled:opacity-50"
        >
          Send
        </button>
      </div>

      {loading && <p className="text-center text-gray-500 text-sm">Listening and thinking…</p>}
      {error && <p className="text-center text-red-600 bg-red-50 rounded-lg py-2 px-3">{error}</p>}

      {turns.length > 0 && (
        <div className="flex flex-col gap-3">
          {lastFallback && (
            <div className="rounded-lg bg-yellow-100 text-yellow-900 text-sm px-3 py-2 font-medium">
              AI model unavailable — showing standard advice
            </div>
          )}
          {turns.map((t, i) => (
            <div key={i} className="flex flex-col gap-1">
              <p className="text-sm text-gray-500 font-medium">You asked: “{t.question}”</p>
              <p className="text-lg leading-relaxed text-gray-900">{t.answer}</p>
            </div>
          ))}
          {lastAudio && (
            <AudioPlayer
              audioUrl={lastAudio.url}
              ttsFallback={lastAudio.fallback}
              fallbackText={lastAudio.text}
            />
          )}
        </div>
      )}
    </div>
  );
}
