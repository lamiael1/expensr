from fastapi.testclient import TestClient

from app.main import app


def test_read_root_devuelve_mensaje_de_bienvenida():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenido a la API de Expensr"}
