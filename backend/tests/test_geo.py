from app.services.geo import lookup_zone
from app.settings import settings


def test_lookup_zone_bengaluru():
    zone = lookup_zone(12.97, 77.59)
    assert zone.id == "bengaluru_rural"


def test_lookup_zone_hyderabad():
    zone = lookup_zone(17.38, 78.48)
    assert zone.id == "hyderabad_rangareddy"


def test_lookup_zone_default_when_no_coords():
    zone = lookup_zone(None, None)
    assert zone.id == settings.DEFAULT_ZONE_ID


def test_lookup_zone_default_when_outside_all_boxes():
    zone = lookup_zone(0.0, 0.0)
    assert zone.id == settings.DEFAULT_ZONE_ID
