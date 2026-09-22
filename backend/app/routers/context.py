from fastapi import APIRouter

from app.services.geo import lookup_zone
from app.services.schemes import schemes_for

router = APIRouter()


@router.get("/context")
def get_context(lat: float | None = None, lon: float | None = None, crop: str | None = None) -> dict:
    zone = lookup_zone(lat, lon)
    schemes = schemes_for(zone.state, crop)
    return {
        "zone": {
            "id": zone.id,
            "name": zone.name,
            "state": zone.state,
            "soil": zone.soil,
            "climate": zone.climate,
            "season_note": zone.season_note,
        },
        "schemes": [{"id": s.id, "name": s.name, "summary": s.summary} for s in schemes],
    }
