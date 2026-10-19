
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense_db import ExpenseDB

router = APIRouter(prefix="/monitor", tags=["Monitor"])


class ExpenseInstance(BaseModel):
    id: int
    empleado: str
    concepto: str
    importe: float
    sistema: str
    etapa_actual: str
    prioridad: str
    estado: str
    fecha_creacion: str


class KPIOverview(BaseModel):
    total_expenses: int
    total_amount: float
    pending_baw: int
    pending_appian: int
    approved: int
    rejected: int
    completados_hoy: int
    instancias: list[ExpenseInstance]


@router.get("/overview", response_model=KPIOverview)
def get_monitor_overview(
    db: Annotated[Session, Depends(get_db)],
):
    totals = db.query(
        func.count(ExpenseDB.id),
        func.coalesce(func.sum(ExpenseDB.importe), 0),
    ).one()

    pending_baw = (
        db.query(func.count(ExpenseDB.id))
        .filter(ExpenseDB.estado == "PENDIENTE_BAW")
        .scalar()
        or 0
    )

    pending_appian = (
        db.query(func.count(ExpenseDB.id))
        .filter(ExpenseDB.estado == "PENDIENTE_APPIAN")
        .scalar()
        or 0
    )

    approved = (
        db.query(func.count(ExpenseDB.id))
        .filter(
            ExpenseDB.estado.in_(["APROBADO", "APROBADO_BAW"])
        )
        .scalar()
        or 0
    )

    rejected = (
        db.query(func.count(ExpenseDB.id))
        .filter(
            ExpenseDB.estado.in_(["RECHAZADO", "RECHAZADO_BAW"])
        )
        .scalar()
        or 0
    )

    today = datetime.now(UTC).date()

    completados_hoy = (
        db.query(func.count(ExpenseDB.id))
        .filter(
            func.date(ExpenseDB.fecha_decision_appian) == today,
            ExpenseDB.decision_final.is_not(None),
        )
        .scalar()
        or 0
    )

    expenses = (
        db.query(ExpenseDB)
        .order_by(ExpenseDB.fecha_creacion.desc())
        .limit(100)
        .all()
    )

    instancias = []

    for expense in expenses:
        estado = expense.estado or "SIN_ESTADO"

        if estado == "PENDIENTE_BAW":
            sistema = "BAW"
            etapa = "Pendiente de validación BAW"
        elif estado == "PENDIENTE_APPIAN":
            sistema = "Appian"
            etapa = "Pendiente de decisión financiera"
        elif estado in (
            "APROBADO",
            "RECHAZADO",
            "APROBADO_BAW",
            "RECHAZADO_BAW",
        ):
            sistema = "Finalizado"
            etapa = "Proceso finalizado"
        else:
            sistema = "Expensr"
            etapa = estado.replace("_", " ").capitalize()

        instancias.append(
            ExpenseInstance(
                id=expense.id,
                empleado=expense.empleado,
                concepto=expense.concepto,
                importe=float(expense.importe),
                sistema=sistema,
                etapa_actual=etapa,
                prioridad=(
                    "Alta"
                    if expense.requiere_revision_manager
                    else "Normal"
                ),
                estado=estado,
                fecha_creacion=(
                    expense.fecha_creacion.isoformat()
                    if expense.fecha_creacion
                    else ""
                ),
            )
        )

    return KPIOverview(
        total_expenses=totals[0],
        total_amount=float(totals[1]),
        pending_baw=pending_baw,
        pending_appian=pending_appian,
        approved=approved,
        rejected=rejected,
        completados_hoy=completados_hoy,
        instancias=instancias,
    )
