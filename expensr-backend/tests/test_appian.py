from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.models.expense_db import ExpenseDB


def crear_gasto(db_session, **cambios):
    datos = {
        "empleado": "empleado_007",
        "fecha": date(2026, 10, 28),
        "concepto": "Comida de trabajo",
        "categoria": "Dietas",
        "importe": Decimal("50.00"),
        "estado": "PENDIENTE_APPIAN",
        "requiere_revision_manager": False,
    }
    datos.update(cambios)

    gasto = ExpenseDB(**datos)
    db_session.add(gasto)
    db_session.commit()
    db_session.refresh(gasto)
    return gasto


def test_obtener_contexto_de_decision(client, db_session):
    gasto = crear_gasto(db_session)

    db_session.execute(
        text(
            """
            CREATE TABLE presupuestos (
                id INTEGER PRIMARY KEY,
                empleado TEXT NOT NULL,
                categoria TEXT NOT NULL,
                limite_mensual NUMERIC NOT NULL
            )
            """
        )
    )
    db_session.execute(
        text(
            """
            INSERT INTO presupuestos (empleado, categoria, limite_mensual)
            VALUES (:empleado, :categoria, :limite)
            """
        ),
        {
            "empleado": gasto.empleado,
            "categoria": gasto.categoria,
            "limite": 500,
        },
    )
    db_session.commit()

    response = client.get(f"/appian/expenses/{gasto.id}/decision-context")

    assert response.status_code == 200
    datos = response.json()
    assert datos["gasto_id"] == gasto.id
    assert datos["empleado"] == gasto.empleado
    assert datos["concepto"] == gasto.concepto
    assert datos["categoria"] == gasto.categoria
    assert datos["importe"] == 50.0
    assert datos["limite_mensual"] == 500.0
    assert datos["acumulado_mes_aprobado"] == 0.0
    assert datos["presupuesto_restante_previo"] == 500.0


def test_obtener_contexto_de_gasto_inexistente(client):
    response = client.get("/appian/expenses/999/decision-context")

    assert response.status_code == 404
    assert response.json()["detail"] == "No existe el gasto #999."


@pytest.mark.parametrize(
    ("decision", "estado_esperado"),
    [
        ("Aprobar", "APROBADO"),
        ("Aprobar con ajuste", "APROBADO"),
        ("Rechazar", "RECHAZADO"),
    ],
)
def test_guardar_decision_appian(
    client,
    db_session,
    decision,
    estado_esperado,
):
    gasto = crear_gasto(db_session)
    payload = {
        "acumulado_mes": "125.50",
        "presupuesto_restante": "75.00",
        "decision_final": decision,
        "comentario_appian": "Revisado por Finanzas",
    }

    response = client.post(
        f"/appian/expenses/{gasto.id}/decision",
        json=payload,
    )

    assert response.status_code == 200
    datos = response.json()
    assert datos["ok"] is True
    assert datos["gasto_id"] == gasto.id
    assert datos["estado"] == estado_esperado
    assert datos["decision_final"] == decision
    assert datos["acumulado_mes"] == 125.5
    assert datos["presupuesto_restante"] == 75.0
    assert datos["comentario_appian"] == "Revisado por Finanzas"
    assert datos["fecha_decision_appian"] is not None

    db_session.refresh(gasto)
    assert gasto.estado == estado_esperado
    assert gasto.acumulado_mes == Decimal("125.50")
    assert gasto.presupuesto_restante == Decimal("75.00")
    assert gasto.decision_final == decision
    assert gasto.comentario_appian == "Revisado por Finanzas"
    assert gasto.fecha_decision_appian is not None


def test_decision_appian_acepta_comentario_vacio(client, db_session):
    gasto = crear_gasto(db_session)
    payload = {
        "acumulado_mes": "0",
        "presupuesto_restante": "500",
        "decision_final": "Aprobar",
        "comentario_appian": "",
    }

    response = client.post(
        f"/appian/expenses/{gasto.id}/decision",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["comentario_appian"] == ""

    db_session.refresh(gasto)
    assert gasto.comentario_appian == ""


def test_decision_appian_rechaza_decision_no_permitida(client, db_session):
    gasto = crear_gasto(db_session)
    payload = {
        "acumulado_mes": "0",
        "presupuesto_restante": "500",
        "decision_final": "DEBUG_INVALIDA",
        "comentario_appian": "",
    }

    response = client.post(
        f"/appian/expenses/{gasto.id}/decision",
        json=payload,
    )

    assert response.status_code == 422


def test_decision_appian_rechaza_acumulado_negativo(client, db_session):
    gasto = crear_gasto(db_session)
    payload = {
        "acumulado_mes": "-1",
        "presupuesto_restante": "500",
        "decision_final": "Aprobar",
        "comentario_appian": "",
    }

    response = client.post(
        f"/appian/expenses/{gasto.id}/decision",
        json=payload,
    )

    assert response.status_code == 422


def test_guardar_decision_de_gasto_inexistente(client):
    payload = {
        "acumulado_mes": "0",
        "presupuesto_restante": "500",
        "decision_final": "Aprobar",
        "comentario_appian": "",
    }

    response = client.post("/appian/expenses/999/decision", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "No existe el gasto #999."
