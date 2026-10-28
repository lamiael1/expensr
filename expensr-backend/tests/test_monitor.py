from datetime import UTC, datetime, timedelta

from app.routers import monitor
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


def test_overview_vacio_incluye_campos_ampliados(client):
    response = client.get("/monitor/overview")

    body = response.json()
    assert body["en_curso"] == 0
    assert body["tiempo_medio_horas"] is None
    assert body["sla_pct"] is None
    assert len(body["series_tiempos"]) == 7


def test_overview_en_curso_y_horas_en_etapa(client, db_session):
    crear_gasto(db_session, estado="PENDIENTE_BAW")
    crear_gasto(db_session, estado="PENDIENTE_APPIAN")
    crear_gasto(db_session, estado="APROBADO")

    response = client.get("/monitor/overview")

    body = response.json()
    assert body["en_curso"] == 2

    por_estado = {i["estado"]: i for i in body["instancias"]}
    assert por_estado["PENDIENTE_BAW"]["horas_en_etapa"] > 0
    assert por_estado["PENDIENTE_APPIAN"]["horas_en_etapa"] > 0
    assert por_estado["APROBADO"]["horas_en_etapa"] is None


def test_overview_tiempo_medio_sla_y_serie(client, db_session):
    creacion = datetime.now(UTC) - timedelta(days=3)

    # Gasto resuelto en 10 h: 4 h en BAW y 6 h en Appian.
    rapido = crear_gasto(db_session, estado="APROBADO", decision_final="APROBADO")
    rapido.fecha_creacion = creacion
    rapido.fecha_validacion_baw = creacion + timedelta(hours=4)
    rapido.fecha_decision_appian = creacion + timedelta(hours=10)

    # Gasto resuelto en 60 h: 4 h en BAW y 56 h en Appian.
    lento = crear_gasto(db_session, estado="APROBADO", decision_final="APROBADO")
    lento.fecha_creacion = creacion
    lento.fecha_validacion_baw = creacion + timedelta(hours=4)
    lento.fecha_decision_appian = creacion + timedelta(hours=60)

    db_session.commit()

    response = client.get("/monitor/overview")

    body = response.json()
    assert body["tiempo_medio_horas"] == 35.0
    assert body["sla_pct"] == 50.0

    dia = creacion.date().isoformat()
    serie = {s["dia"]: s for s in body["series_tiempos"]}
    assert serie[dia]["baw_horas"] == 4.0
    assert serie[dia]["appian_horas"] == 31.0


def test_series_omite_gasto_si_fecha_creacion_no_se_puede_convertir(
    db_session,
    monkeypatch,
):
    crear_gasto(db_session)
    monkeypatch.setattr(monitor, "_aware", lambda valor: None)

    series = monitor._series_tiempos(db_session, datetime.now(UTC))

    assert len(series) == 7
    assert all(dia.baw_horas == 0.0 for dia in series)
    assert all(dia.appian_horas == 0.0 for dia in series)


def test_series_omite_gasto_fuera_de_los_siete_dias(db_session):
    gasto = crear_gasto(db_session)
    gasto.fecha_creacion = datetime.now(UTC) + timedelta(days=2)
    db_session.commit()

    series = monitor._series_tiempos(db_session, datetime.now(UTC))

    assert len(series) == 7
    assert all(dia.baw_horas == 0.0 for dia in series)
    assert all(dia.appian_horas == 0.0 for dia in series)


def test_overview_muestra_estado_desconocido_como_expensr(client, db_session):
    crear_gasto(db_session, estado="EN_REVISION_INTERNA")

    response = client.get("/monitor/overview")

    assert response.status_code == 200
    instancia = response.json()["instancias"][0]
    assert instancia["sistema"] == "Expensr"
    assert instancia["etapa_actual"] == "En revision interna"
