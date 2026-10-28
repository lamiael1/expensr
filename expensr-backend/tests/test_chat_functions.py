from datetime import UTC, date, datetime

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
        db=db_session,
        empleado="empleado_007",
        categoria="dietas",
    )

    assert resultado["total"] == 1
    assert resultado["gastos"][0]["categoria"] == "Dietas"


def test_listar_gastos_filtra_por_mes(db_session):
    crear_gasto(
        db_session,
        concepto="Gasto de octubre",
        fecha=date(2026, 10, 10),
    )
    crear_gasto(
        db_session,
        concepto="Gasto de septiembre",
        fecha=date(2026, 9, 10),
    )

    resultado = listar_gastos(
        db=db_session,
        empleado="empleado_007",
        mes=10,
    )

    assert resultado["total"] == 1
    assert resultado["gastos"][0]["concepto"] == "Gasto de octubre"


def test_listar_gastos_devuelve_como_maximo_20(db_session):
    for numero in range(22):
        crear_gasto(
            db_session,
            concepto=f"Gasto {numero}",
            fecha=date(2026, 10, 10),
        )

    resultado = listar_gastos(db=db_session, empleado="empleado_007")

    assert resultado["total"] == 20
    assert len(resultado["gastos"]) == 20


def test_consultar_estado_gasto_concreto(db_session):
    gasto = crear_gasto(db_session, concepto="Factura hotel")

    resultado = consultar_estado(
        db=db_session,
        empleado="empleado_007",
        gasto_id=gasto.id,
    )

    assert resultado["encontrado"] is True
    assert resultado["concepto"] == "Factura hotel"


def test_consultar_estado_gasto_inexistente(db_session):
    resultado = consultar_estado(
        db=db_session,
        empleado="empleado_007",
        gasto_id=9999,
    )

    assert resultado["encontrado"] is False


def test_consultar_estado_no_devuelve_datos_de_otro_empleado(db_session):
    gasto = crear_gasto(db_session, empleado="empleado_099")

    resultado = consultar_estado(
        db=db_session,
        empleado="empleado_007",
        gasto_id=gasto.id,
    )

    assert resultado["encontrado"] is False


def test_consultar_estado_sin_id_devuelve_gasto_pendiente_mas_reciente(
    db_session,
):
    antiguo = crear_gasto(
        db_session,
        concepto="Gasto ya resuelto",
        decision_final="Aprobar",
    )
    antiguo.fecha_creacion = datetime(2026, 10, 1, tzinfo=UTC)

    pendiente = crear_gasto(
        db_session,
        concepto="Gasto pendiente reciente",
        decision_final=None,
    )
    pendiente.fecha_creacion = datetime(2026, 10, 5, tzinfo=UTC)
    db_session.commit()

    resultado = consultar_estado(db=db_session, empleado="empleado_007")

    assert resultado["encontrado"] is True
    assert resultado["id"] == pendiente.id
    assert resultado["concepto"] == "Gasto pendiente reciente"


def test_consultar_estado_sin_id_indica_si_no_hay_pendientes(db_session):
    crear_gasto(
        db_session,
        decision_final="Aprobar",
        estado="APROBADO",
    )

    resultado = consultar_estado(db=db_session, empleado="empleado_007")

    assert resultado == {
        "encontrado": False,
        "mensaje": "No hay gastos pendientes.",
    }


def test_tiempo_medio_aprobacion_sin_gastos_resueltos(db_session):
    crear_gasto(db_session, decision_final=None)

    resultado = tiempo_medio_aprobacion(
        db=db_session,
        empleado="empleado_007",
    )

    assert resultado["muestras"] == 0
    assert resultado["tiempo_medio_dias"] is None
    assert resultado["mensaje"] == "Aún no hay gastos resueltos."


def test_tiempo_medio_aprobacion_calcula_dias(db_session):
    creacion = datetime(2026, 10, 1, tzinfo=UTC)
    decision = datetime(2026, 10, 3, tzinfo=UTC)

    gasto = crear_gasto(db_session, decision_final="APROBADO")
    gasto.fecha_creacion = creacion
    gasto.fecha_decision_appian = decision
    db_session.commit()

    resultado = tiempo_medio_aprobacion(
        db=db_session,
        empleado="empleado_007",
    )

    assert resultado["muestras"] == 1
    assert resultado["tiempo_medio_dias"] == 2.0


def test_tiempo_medio_aprobacion_usa_fecha_validacion_baw_como_fallback(
    db_session,
):
    creacion = datetime(2026, 10, 1, tzinfo=UTC)
    validacion_baw = datetime(2026, 10, 2, tzinfo=UTC)

    gasto = crear_gasto(
        db_session,
        decision_final="Aprobar",
        fecha_validacion_baw=validacion_baw,
    )
    gasto.fecha_creacion = creacion
    db_session.commit()

    resultado = tiempo_medio_aprobacion(
        db=db_session,
        empleado="empleado_007",
    )

    assert resultado["muestras"] == 1
    assert resultado["tiempo_medio_dias"] == 1.0


def test_tiempo_medio_aprobacion_sin_marcas_de_tiempo(db_session):
    crear_gasto(
        db_session,
        decision_final="Aprobar",
        fecha_validacion_baw=None,
        fecha_decision_appian=None,
    )

    resultado = tiempo_medio_aprobacion(
        db=db_session,
        empleado="empleado_007",
    )

    assert resultado["muestras"] == 0
    assert resultado["tiempo_medio_dias"] is None
    assert resultado["mensaje"] == "No hay timestamps suficientes."


def test_tiempo_medio_aprobacion_no_mezcla_empleados(db_session):
    creacion = datetime(2026, 10, 1, tzinfo=UTC)
    decision = datetime(2026, 10, 4, tzinfo=UTC)

    gasto = crear_gasto(
        db_session,
        empleado="empleado_099",
        decision_final="Aprobar",
    )
    gasto.fecha_creacion = creacion
    gasto.fecha_decision_appian = decision
    db_session.commit()

    resultado = tiempo_medio_aprobacion(
        db=db_session,
        empleado="empleado_007",
    )

    assert resultado["muestras"] == 0
    assert resultado["tiempo_medio_dias"] is None
