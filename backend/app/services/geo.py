"""GPS fallback ladder step: point-in-bbox zone lookup. Falls back to DEFAULT_ZONE_ID."""
import sqlite3
from dataclasses import dataclass

from app.settings import settings


@dataclass
class Zone:
    id: str
    name: str
    state: str
    soil: str
    climate: str
    season_note: str


def _row_to_zone(row: sqlite3.Row) -> Zone:
    return Zone(
        id=row["id"], name=row["name"], state=row["state"],
        soil=row["soil"], climate=row["climate"], season_note=row["season_note"],
    )


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def lookup_zone(lat: float | None, lon: float | None) -> Zone:
    conn = _connect()
    try:
        if lat is not None and lon is not None:
            row = conn.execute(
                "SELECT * FROM zones WHERE ? BETWEEN min_lat AND max_lat "
                "AND ? BETWEEN min_lon AND max_lon LIMIT 1",
                (lat, lon),
            ).fetchone()
            if row:
                return _row_to_zone(row)

        default_row = conn.execute(
            "SELECT * FROM zones WHERE id = ?", (settings.DEFAULT_ZONE_ID,)
        ).fetchone()
        if default_row is None:
            raise RuntimeError(f"DEFAULT_ZONE_ID '{settings.DEFAULT_ZONE_ID}' not found in agri.db")
        return _row_to_zone(default_row)
    finally:
        conn.close()
