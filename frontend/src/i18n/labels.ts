import type { LangCode } from "../types";

export const LANG_LABELS: Record<LangCode, string> = {
  kn: "ಕನ್ನಡ",
  hi: "हिन्दी",
  te: "తెలుగు",
  ta: "தமிழ்",
  en: "EN",
};

export const UI_STRINGS: Record<LangCode, { scanLeaf: string; title: string }> = {
  kn: { scanLeaf: "ಎಲೆ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ", title: "ಅಗ್ರಿ-ವಿಷನ್" },
  hi: { scanLeaf: "पत्ती स्कैन करें", title: "अग्री-विज़न" },
  te: { scanLeaf: "ఆకును స్కాన్ చేయండి", title: "అగ్రి-విజన్" },
  ta: { scanLeaf: "இலையை ஸ்கேன் செய்யவும்", title: "அக்ரி-விஷன்" },
  en: { scanLeaf: "Scan leaf", title: "Agri-Vision" },
};
