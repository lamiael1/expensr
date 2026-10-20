from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense_db import ExpenseDB

router = APIRouter(prefix="/baw", tags=["BAW"])


class BawValidationUpdate(BaseModel):
    centro_coste: str

    requiere_revision_manager: bool

    estado: str


class BawDecisionUpdate(BaseModel):
    estado: str

    comentario_baw: str | None = None


def _get_expense_or_404(db: Session, gasto_id: int) -> ExpenseDB:

    gasto = db.query(ExpenseDB).filter(ExpenseDB.id == gasto_id).first()

    if gasto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el gasto #{gasto_id}.",
        )

    return gasto


@router.patch("/expenses/{gasto_id}/validation")
def update_baw_validation(
    gasto_id: int,
    payload: BawValidationUpdate,
    db: Annotated[Session, Depends(get_db)],
):

    gasto = _get_expense_or_404(db, gasto_id)

    gasto.centro_coste = payload.centro_coste

    gasto.requiere_revision_manager = payload.requiere_revision_manager

    gasto.estado = payload.estado

    gasto.fecha_validacion_baw = datetime.now(UTC)

    db.commit()

    db.refresh(gasto)

    return {"ok": True, "gasto_id": gasto.id, "estado": gasto.estado}


@router.patch("/expenses/{gasto_id}/decision")
def update_baw_decision(
    gasto_id: int,
    payload: BawDecisionUpdate,
    db: Annotated[Session, Depends(get_db)],
):

    gasto = _get_expense_or_404(db, gasto_id)

    gasto.estado = payload.estado

    gasto.comentario_baw = payload.comentario_baw

    db.commit()

    db.refresh(gasto)

    return {"ok": True, "gasto_id": gasto.id, "estado": gasto.estado}
