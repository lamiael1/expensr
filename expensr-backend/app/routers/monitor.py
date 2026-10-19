
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense_db import ExpenseDB

router = APIRouter(prefix="/monitor", tags=["Monitor"])


class KPIOverview(BaseModel):
    total_expenses: int
    total_amount: float
    pending_baw: int
    pending_appian: int
    approved: int
    rejected: int


@router.get("/overview", response_model=KPIOverview)
def get_monitor_overview(
    db: Annotated[Session, Depends(get_db)],
):
    totals = db.query(
        func.count(ExpenseDB.id),
        func.coalesce(func.sum(ExpenseDB.importe), 0),
    ).one()

    pending_baw = db.query(func.count(ExpenseDB.id)).filter(
        ExpenseDB.estado == "PENDIENTE_BAW"
    ).scalar()

    pending_appian = db.query(func.count(ExpenseDB.id)).filter(
        ExpenseDB.estado == "PENDIENTE_APPIAN"
    ).scalar()

    approved = db.query(func.count(ExpenseDB.id)).filter(
        ExpenseDB.estado.in_(["APROBADO", "APROBADO_BAW"])
    ).scalar()

    rejected = db.query(func.count(ExpenseDB.id)).filter(
        ExpenseDB.estado.in_(["RECHAZADO", "RECHAZADO_BAW"])
    ).scalar()

    return KPIOverview(
        total_expenses=totals[0],
        total_amount=float(totals[1]),
        pending_baw=pending_baw or 0,
        pending_appian=pending_appian or 0,
        approved=approved or 0,
        rejected=rejected or 0,
    )
