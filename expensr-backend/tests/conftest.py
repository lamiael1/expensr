import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app

VARIABLES_EXTERNAS = (
    "BAW_BASE_URL",
    "BAW_USER",
    "BAW_PASSWORD",
    "APPIAN_BASE_URL",
    "APPIAN_API_KEY",
)


@pytest.fixture(autouse=True)
def sin_credenciales_externas(monkeypatch):
    """Los tests nunca deben depender del .env ni llamar a BAW/Appian reales."""
    for nombre in VARIABLES_EXTERNAS:
        monkeypatch.delenv(nombre, raising=False)


@pytest.fixture()
def db_session():
    """Base de datos SQLite en memoria, aislada por test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """Cliente HTTP de test con la DB en memoria inyectada vía override."""

    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
