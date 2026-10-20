from datetime import UTC, datetime

from app.services.chat_functions import (
    consultar_estado,
    listar_gastos,
    tiempo_medio_aprobacion,
)
from tests.factories import crear_gasto


def test_listar_gastos_filtra_por_empleado(db_session):
    crear_gasto(db_session, empleado="empleado_007", concepto="Mío")
    crear_gasto(db_session, empleado="empleado_099", concepto="De otro")

    resultado = listar_gastos(db=db_session, empleado="empleado_007")

    assert resultado["total"] == 1
    assert resultado["gastos"][0]["concepto"] == "Mío"


def test_listar_gastos_filtra_por_categoria(db_session):
    crear_gasto(db_session, categoria="Dietas")
    crear_gasto(db_session, categoria="Transporte")

    resultado = listar_gastos(
        db=db_session, empleado="empleado_007", categoria="dietas"
    )

    assert resultado["total"] == 1
    assert resultado["gastos"][0]["categoria"] == "Dietas"


def test_consultar_estado_gasto_concreto(db_session):
    gasto = crear_gasto(db_session, concepto="Factura hotel")

    resultado = consultar_estado(
        db=db_session, empleado="empleado_007", gasto_id=gasto.id
    )

    assert resultado["encontrado"] is True
    assert resultado["concepto"] == "Factura hotel"


def test_consultar_estado_gasto_inexistente(db_session):
    resultado = consultar_estado(db=db_session, empleado="empleado_007", gasto_id=9999)

    assert resultado["encontrado"] is False


def test_consultar_estado_no_devuelve_datos_de_otro_empleado(db_session):
    gasto = crear_gasto(db_session, empleado="empleado_099")

    resultado = consultar_estado(
        db=db_session, empleado="empleado_007", gasto_id=gasto.id
    )

    assert resultado["encontrado"] is False


def test_tiempo_medio_aprobacion_sin_gastos_resueltos(db_session):
    crear_gasto(db_session, decision_final=None)

    resultado = tiempo_medio_aprobacion(db=db_session, empleado="empleado_007")

    assert resultado["muestras"] == 0
    assert resultado["tiempo_medio_dias"] is None


def test_tiempo_medio_aprobacion_calcula_dias(db_session):
    creacion = datetime(2026, 10, 1, tzinfo=UTC)
    decision = datetime(2026, 10, 3, tzinfo=UTC)  # 2 días después

    gasto = crear_gasto(db_session, decision_final="APROBADO")
    gasto.fecha_creacion = creacion
    gasto.fecha_decision_appian = decision
    db_session.commit()

    resultado = tiempo_medio_aprobacion(db=db_session, empleado="empleado_007")

    assert resultado["muestras"] == 1
    assert resultado["tiempo_medio_dias"] == 2.0
