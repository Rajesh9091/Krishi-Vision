import { LANG_LABELS } from "../i18n/labels";
import type { LangCode } from "../types";

interface Props {
  value: LangCode;
  onChange: (lang: LangCode) => void;
}

const LANGS: LangCode[] = ["kn", "hi", "te", "ta", "en"];

export default function LanguagePills({ value, onChange }: Props) {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {LANGS.map((lang) => (
        <button
          key={lang}
          onClick={() => onChange(lang)}
          className={`rounded-full px-4 py-2 text-lg font-semibold border-2 ${
            value === lang
              ? "bg-green-700 text-white border-green-700"
              : "bg-white text-green-800 border-green-300"
          }`}
        >
          {LANG_LABELS[lang]}
        </button>
      ))}
    </div>
  );
}
