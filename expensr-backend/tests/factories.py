from datetime import UTC, datetime, timedelta

from app.models.expense_db import ExpenseDB


def crear_gasto(
    db_session,
    *,
    empleado="empleado_007",
    fecha=None,
    concepto="Gasto de prueba",
    categoria="Dietas",
    importe=50.0,
    estado="PENDIENTE_BAW",
    decision_final=None,
    fecha_validacion_baw=None,
    fecha_decision_appian=None,
    requiere_revision_manager=False,
):
    gasto = ExpenseDB(
        empleado=empleado,
        fecha=fecha or datetime.now(UTC).date(),
        concepto=concepto,
        categoria=categoria,
        importe=importe,
        estado=estado,
        decision_final=decision_final,
        fecha_validacion_baw=fecha_validacion_baw,
        fecha_decision_appian=fecha_decision_appian,
        requiere_revision_manager=requiere_revision_manager,
        fecha_creacion=datetime.now(UTC) - timedelta(days=1),
    )
    db_session.add(gasto)
    db_session.commit()
    db_session.refresh(gasto)
    return gasto
