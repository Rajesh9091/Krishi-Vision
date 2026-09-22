import { useRef, useState } from "react";

interface Props {
  label: string;
  onCapture: (file: File) => void;
}

export default function Capture({ label, onCapture }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    onCapture(file);
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={() => inputRef.current?.click()}
        className="w-full rounded-2xl bg-green-700 px-6 py-5 text-2xl font-bold text-white shadow active:scale-95"
      >
        📷 {label}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleChange}
      />
      {preview && (
        <img src={preview} alt="leaf preview" className="w-40 h-40 object-cover rounded-xl border" />
      )}
    </div>
  );
}
