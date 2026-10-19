import os

# 1. Адрес тестовой базы нужно задать ДО импорта приложения,
#    иначе database.py уже создаст движок с боевым адресом.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://app_user:app_pass@localhost:5433/app_test",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from apps.database import engine
from apps.main import app
from apps.models import Base

# 2. Страховка: не работать, если база не тестовая.
db_name = make_url(os.environ["DATABASE_URL"]).database
if not db_name.endswith("_test"):
    raise RuntimeError(f"Refusing to run tests on non-test database: {db_name}")


@pytest.fixture
def client():
    # 3. Чистые таблицы перед каждым тестом
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # 4. С `with` срабатывает lifespan приложения (init_db)
    with TestClient(app) as c:
        yield c
