import { useEffect, useState } from "react";

import { getContext } from "../api";
import type { Zone } from "../types";

interface Props {
  onLocated: (lat?: number, lon?: number) => void;
}

export default function GeoChip({ onLocated }: Props) {
  const [zone, setZone] = useState<Zone | null>(null);
  const [manual, setManual] = useState(false);
  const [latInput, setLatInput] = useState("");
  const [lonInput, setLonInput] = useState("");

  async function loadZone(lat?: number, lon?: number) {
    try {
      const ctx = await getContext(lat, lon);
      setZone(ctx.zone);
      onLocated(lat, lon);
    } catch {
      onLocated(lat, lon);
    }
  }

  useEffect(() => {
    if (!navigator.geolocation) {
      loadZone();
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => loadZone(pos.coords.latitude, pos.coords.longitude),
      () => loadZone(),
      { timeout: 5000 },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submitManual() {
    const lat = parseFloat(latInput);
    const lon = parseFloat(lonInput);
    if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
      loadZone(lat, lon);
      setManual(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-1 text-center">
      <span className="rounded-full bg-green-100 px-3 py-1 text-sm text-green-800">
        📍 {zone ? `${zone.name}${zone.soil ? " · " + zone.soil : ""}` : "Locating…"}
      </span>
      {!manual ? (
        <button className="text-xs text-blue-600 underline" onClick={() => setManual(true)}>
          Set location manually
        </button>
      ) : (
        <div className="flex gap-2 items-center">
          <input
            className="w-20 rounded border px-1 text-sm"
            placeholder="lat"
            value={latInput}
            onChange={(e) => setLatInput(e.target.value)}
          />
          <input
            className="w-20 rounded border px-1 text-sm"
            placeholder="lon"
            value={lonInput}
            onChange={(e) => setLonInput(e.target.value)}
          />
          <button className="text-xs text-green-700 underline" onClick={submitManual}>
            Go
          </button>
        </div>
      )}
    </div>
  );
}
