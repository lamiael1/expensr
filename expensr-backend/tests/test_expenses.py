def test_get_expenses_vacio(client):
    response = client.get("/expenses/")

    assert response.status_code == 200
    assert response.json() == []


def test_crear_gasto(client):
    payload = {
        "empleado": "empleado_007",
        "fecha": "2026-10-15",
        "concepto": "Taxi al aeropuerto",
        "categoria": "Transporte",
        "importe": 32.5,
    }

    response = client.post("/expenses/", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["empleado"] == "empleado_007"
    assert body["concepto"] == "Taxi al aeropuerto"
    assert body["importe"] == 32.5
    assert body["estado"] == "PENDIENTE_BAW"
    assert body["id"] is not None


def test_listar_gastos_tras_crear(client, db_session):
    from tests.factories import crear_gasto

    crear_gasto(db_session, concepto="Comida cliente")
    crear_gasto(db_session, concepto="Billete de tren")

    response = client.get("/expenses/")

    assert response.status_code == 200
    conceptos = {g["concepto"] for g in response.json()}
    assert conceptos == {"Comida cliente", "Billete de tren"}


def test_crear_gasto_sin_campos_obligatorios_falla(client):
    response = client.post("/expenses/", json={"empleado": "empleado_007"})

    assert response.status_code == 422
