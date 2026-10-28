import pytest

from tests.factories import crear_gasto


def test_get_expenses_vacio(client):
    response = client.get("/expenses/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("instance_id", ["2546", None])
def test_crear_gasto_guarda_id_de_baw_si_lo_recibe(
    client,
    monkeypatch,
    instance_id,
):
    payload = {
        "empleado": "empleado_007",
        "fecha": "2026-10-15",
        "concepto": "Taxi al aeropuerto",
        "categoria": "Transporte",
        "importe": 32.5,
    }
    gasto_enviado_a_baw = {}

    def iniciar_baw(gasto):
        gasto_enviado_a_baw.update(gasto)
        return instance_id

    monkeypatch.setattr(
        "app.routers.expenses.start_baw_instance",
        iniciar_baw,
    )

    response = client.post("/expenses/", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["empleado"] == "empleado_007"
    assert body["concepto"] == "Taxi al aeropuerto"
    assert body["importe"] == 32.5
    assert body["estado"] == "PENDIENTE_BAW"
    assert body["baw_instance_id"] == instance_id
    assert gasto_enviado_a_baw == {
        "id": body["id"],
        "empleado": "empleado_007",
        "fecha": "2026-10-15",
        "concepto": "Taxi al aeropuerto",
        "categoria": "Transporte",
        "importe": 32.5,
    }


def test_crear_gasto_se_guarda_si_baw_falla(client, monkeypatch, caplog):
    payload = {
        "empleado": "empleado_007",
        "fecha": "2026-10-15",
        "concepto": "Taxi al aeropuerto",
        "categoria": "Transporte",
        "importe": 32.5,
    }

    def fallar_baw(gasto):
        raise RuntimeError("BAW temporalmente no disponible")

    monkeypatch.setattr(
        "app.routers.expenses.start_baw_instance",
        fallar_baw,
    )

    response = client.post("/expenses/", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    assert body["estado"] == "PENDIENTE_BAW"
    assert body["baw_instance_id"] is None
    assert "BAW temporalmente no disponible" in caplog.text


def test_listar_gastos_tras_crear(client, db_session):
    crear_gasto(db_session, concepto="Comida cliente")
    crear_gasto(db_session, concepto="Billete de tren")

    response = client.get("/expenses/")

    assert response.status_code == 200
    conceptos = {g["concepto"] for g in response.json()}
    assert conceptos == {"Comida cliente", "Billete de tren"}


def test_crear_gasto_sin_campos_obligatorios_falla(client):
    response = client.post("/expenses/", json={"empleado": "empleado_007"})

    assert response.status_code == 422


def test_get_expense_detalle(client, db_session):
    gasto = crear_gasto(db_session, concepto="Factura hotel")

    response = client.get(f"/expenses/{gasto.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == gasto.id
    assert body["concepto"] == "Factura hotel"
    assert body["estado"] == "PENDIENTE_BAW"


def test_get_expense_inexistente(client):
    response = client.get("/expenses/9999")

    assert response.status_code == 404
