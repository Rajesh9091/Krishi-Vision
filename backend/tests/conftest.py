import subprocess
import sys
from pathlib import Path

import pytest

from app.settings import settings


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    if not settings.DB_PATH.exists():
        seed_script = Path(settings.DATA_DIR) / "seed_agri_db.py"
        subprocess.run([sys.executable, str(seed_script)], check=True)
    yield
