export interface HistoryEntry {
  crop: string;
  disease: string;
  confidencePct: number;
  time: string;
}

interface Props {
  entries: HistoryEntry[];
}

export default function ScanHistory({ entries }: Props) {
  if (entries.length === 0) return null;

  return (
    <div className="rounded-2xl bg-white shadow p-5 flex flex-col gap-2 border border-green-100">
      <p className="text-lg font-bold text-green-900">Recent scans</p>
      <ul className="flex flex-col gap-2">
        {entries.map((e, i) => (
          <li key={i} className="flex justify-between items-baseline text-sm border-b last:border-0 pb-1">
            <span className="font-medium text-gray-800">
              {e.crop} · {e.disease}
            </span>
            <span className="text-gray-500">
              {e.confidencePct}% · {e.time}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
