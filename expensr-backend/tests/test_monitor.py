from tests.factories import crear_gasto


def test_overview_vacio(client):
    response = client.get("/monitor/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_expenses"] == 0
    assert body["instancias"] == []


def test_overview_cuenta_pendientes_y_aprobados(client, db_session):
    crear_gasto(db_session, estado="PENDIENTE_BAW")
    crear_gasto(db_session, estado="PENDIENTE_APPIAN")
    crear_gasto(db_session, estado="APROBADO")
    crear_gasto(db_session, estado="RECHAZADO")

    response = client.get("/monitor/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_expenses"] == 4
    assert body["pending_baw"] == 1
    assert body["pending_appian"] == 1
    assert body["approved"] == 1
    assert body["rejected"] == 1
