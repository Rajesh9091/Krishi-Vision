"""Looks up government schemes applicable to a zone's state and a crop."""
import json
import sqlite3
from dataclasses import dataclass

from app.settings import settings


@dataclass
class Scheme:
    id: str
    name: str
    summary: str


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def schemes_for(state: str, crop: str | None = None) -> list[Scheme]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM schemes").fetchall()
    finally:
        conn.close()

    matches: list[Scheme] = []
    for row in rows:
        states = json.loads(row["states"])
        crops = json.loads(row["crops"])
        if state not in states:
            continue
        if crop is not None and crop not in crops:
            continue
        matches.append(Scheme(id=row["id"], name=row["name"], summary=row["summary"]))
    return matches
