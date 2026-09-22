import { useEffect, useRef, useState } from "react";

interface Props {
  audioUrl: string | null;
  ttsFallback?: "browser" | null;
  fallbackText: string;
}

export default function AudioPlayer({ audioUrl, ttsFallback, fallbackText }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    if (!audioUrl || !audioRef.current) return;
    audioRef.current.play().catch(() => setBlocked(true));
  }, [audioUrl]);

  function replay() {
    if (audioUrl && audioRef.current) {
      setBlocked(false);
      audioRef.current.play().catch(() => setBlocked(true));
      return;
    }
    if (ttsFallback === "browser" && "speechSynthesis" in window) {
      const utter = new SpeechSynthesisUtterance(fallbackText);
      window.speechSynthesis.speak(utter);
    }
  }

  if (!audioUrl && ttsFallback !== "browser") return null;

  return (
    <div className="flex justify-center">
      {audioUrl && <audio ref={audioRef} src={audioUrl} />}
      <button
        onClick={replay}
        className="rounded-full bg-green-700 text-white px-6 py-3 text-lg font-semibold shadow active:scale-95"
      >
        {blocked ? "▶ Play audio" : "🔁 Replay audio"}
      </button>
    </div>
  );
}
