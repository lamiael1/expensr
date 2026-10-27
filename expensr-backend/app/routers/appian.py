from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense_db import ExpenseDB

router = APIRouter(prefix="/appian", tags=["Appian"])


class AppianDecisionContext(BaseModel):
    gasto_id: int
    empleado: str
    fecha: date
    concepto: str
    categoria: str
    importe: float
    estado: str
    limite_mensual: float | None
    acumulado_mes_aprobado: float
    presupuesto_restante_previo: float | None


class AppianDecisionUpdate(BaseModel):
    acumulado_mes: Decimal = Field(ge=0)
    presupuesto_restante: Decimal | None = None
    decision_final: Literal["Aprobar", "Aprobar con ajuste", "Rechazar"]
    comentario_appian: str | None = None


class AppianDecisionResponse(BaseModel):
    ok: bool
    gasto_id: int
    estado: str
    decision_final: str
    acumulado_mes: float
    presupuesto_restante: float | None
    comentario_appian: str | None
    fecha_decision_appian: datetime


def _get_expense_or_404(db: Session, gasto_id: int) -> ExpenseDB:
    gasto = db.query(ExpenseDB).filter(ExpenseDB.id == gasto_id).first()

    if gasto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el gasto #{gasto_id}.",
        )

    return gasto


@router.get(
    "/expenses/{gasto_id}/decision-context",
    response_model=AppianDecisionContext,
)
def get_appian_decision_context(
    gasto_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    gasto = _get_expense_or_404(db, gasto_id)

    inicio_mes = date(gasto.fecha.year, gasto.fecha.month, 1)
    if gasto.fecha.month == 12:
        inicio_mes_siguiente = date(gasto.fecha.year + 1, 1, 1)
    else:
        inicio_mes_siguiente = date(gasto.fecha.year, gasto.fecha.month + 1, 1)

    acumulado = (
        db.query(func.coalesce(func.sum(ExpenseDB.importe), 0))
        .filter(
            ExpenseDB.id != gasto.id,
            ExpenseDB.empleado == gasto.empleado,
            ExpenseDB.categoria == gasto.categoria,
            ExpenseDB.fecha >= inicio_mes,
            ExpenseDB.fecha < inicio_mes_siguiente,
            func.lower(ExpenseDB.decision_final).in_(
                [
                    "aprobar",
                    "aprobar con ajuste",
                    "aprobar_con_ajuste",
                ]
            ),
        )
        .scalar()
    )

    limite = db.execute(
        text(
            """
            SELECT limite_mensual
            FROM presupuestos
            WHERE empleado = :empleado
              AND categoria = :categoria
            """
        ),
        {"empleado": gasto.empleado, "categoria": gasto.categoria},
    ).scalar_one_or_none()

    acumulado_decimal = Decimal(str(acumulado or 0))
    limite_decimal = Decimal(str(limite)) if limite is not None else None
    restante = (
        limite_decimal - acumulado_decimal if limite_decimal is not None else None
    )

    return AppianDecisionContext(
        gasto_id=gasto.id,
        empleado=gasto.empleado,
        fecha=gasto.fecha,
        concepto=gasto.concepto,
        categoria=gasto.categoria,
        importe=float(gasto.importe),
        estado=gasto.estado,
        limite_mensual=float(limite_decimal) if limite_decimal is not None else None,
        acumulado_mes_aprobado=float(acumulado_decimal),
        presupuesto_restante_previo=float(restante) if restante is not None else None,
    )


@router.post(
    "/expenses/{gasto_id}/decision",
    response_model=AppianDecisionResponse,
)
def update_appian_decision(
    gasto_id: int,
    payload: AppianDecisionUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    gasto = _get_expense_or_404(db, gasto_id)

    estado = "RECHAZADO" if payload.decision_final == "Rechazar" else "APROBADO"
    fecha_decision_appian = datetime.now(UTC)

    gasto.acumulado_mes = payload.acumulado_mes
    gasto.presupuesto_restante = payload.presupuesto_restante
    gasto.decision_final = payload.decision_final
    gasto.comentario_appian = payload.comentario_appian
    gasto.fecha_decision_appian = fecha_decision_appian
    gasto.estado = estado

    db.commit()
    db.refresh(gasto)

    return AppianDecisionResponse(
        ok=True,
        gasto_id=gasto.id,
        estado=estado,
        decision_final=payload.decision_final,
        acumulado_mes=float(payload.acumulado_mes),
        presupuesto_restante=(
            float(payload.presupuesto_restante)
            if payload.presupuesto_restante is not None
            else None
        ),
        comentario_appian=payload.comentario_appian,
        fecha_decision_appian=fecha_decision_appian,
    )
