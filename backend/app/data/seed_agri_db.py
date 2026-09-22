"""Rebuilds agri.db from the seed JSON files. Idempotent — safe to re-run."""
import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "agri.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS zones (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    min_lat REAL NOT NULL,
    max_lat REAL NOT NULL,
    min_lon REAL NOT NULL,
    max_lon REAL NOT NULL,
    soil TEXT NOT NULL,
    climate TEXT NOT NULL,
    season_note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schemes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    states TEXT NOT NULL,
    crops TEXT NOT NULL,
    summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diseases (
    key TEXT PRIMARY KEY,
    raw_label TEXT NOT NULL,
    crop TEXT NOT NULL,
    disease TEXT NOT NULL,
    cause TEXT NOT NULL,
    treatments TEXT NOT NULL,
    prevention TEXT NOT NULL
);
"""


def seed() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM zones")
    conn.execute("DELETE FROM schemes")
    conn.execute("DELETE FROM diseases")

    zones = json.loads((DATA_DIR / "zones.json").read_text(encoding="utf-8"))
    for z in zones:
        conn.execute(
            "INSERT INTO zones VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                z["id"], z["name"], z["state"],
                z["bbox"]["min_lat"], z["bbox"]["max_lat"],
                z["bbox"]["min_lon"], z["bbox"]["max_lon"],
                z["soil"], z["climate"], z["season_note"],
            ),
        )

    schemes = json.loads((DATA_DIR / "schemes.json").read_text(encoding="utf-8"))
    for s in schemes:
        conn.execute(
            "INSERT INTO schemes VALUES (?, ?, ?, ?, ?)",
            (s["id"], s["name"], json.dumps(s["states"]), json.dumps(s["crops"]), s["summary"]),
        )

    diseases = json.loads((DATA_DIR / "disease_kb.json").read_text(encoding="utf-8"))
    for d in diseases:
        conn.execute(
            "INSERT INTO diseases VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                d["key"], d["raw_label"], d["crop"], d["disease"], d["cause"],
                json.dumps(d["treatments"]), d["prevention"],
            ),
        )

    conn.commit()
    conn.close()
    print(f"Seeded {DB_PATH} with {len(zones)} zones, {len(schemes)} schemes, {len(diseases)} diseases.")


if __name__ == "__main__":
    seed()
