import { useEffect, useState } from "react";

const STAGES = ["Looking at leaf…", "Thinking…", "Speaking…"];

export default function StageLoader() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStage((s) => Math.min(s + 1, STAGES.length - 1));
    }, 2500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col items-center gap-3 py-8">
      <div className="h-10 w-10 rounded-full border-4 border-green-600 border-t-transparent animate-spin" />
      <p className="text-lg text-green-800 font-medium">{STAGES[stage]}</p>
    </div>
  );
}
