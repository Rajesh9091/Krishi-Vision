import { useEffect } from "react";

interface Props {
  message: string;
  onDismiss: () => void;
}

export default function Toast({ message, onDismiss }: Props) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 4000);
    return () => clearTimeout(timer);
  }, [message, onDismiss]);

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 max-w-[90vw]">
      <div className="rounded-xl bg-red-700 text-white text-base font-medium px-4 py-3 shadow-lg flex items-center gap-3">
        <span>⚠ {message}</span>
        <button onClick={onDismiss} className="text-white/80 font-bold px-1">
          ✕
        </button>
      </div>
    </div>
  );
}
