import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense import ExpenseCreate, ExpenseResponse
from app.models.expense_db import ExpenseDB
from app.services.baw_service import start_baw_instance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/", response_model=list[ExpenseResponse])
def get_expenses(db: Annotated[Session, Depends(get_db)]):
    return (
        db.query(ExpenseDB)
        .order_by(ExpenseDB.fecha.desc(), ExpenseDB.fecha_creacion.desc())
        .all()
    )


@router.get("/{gasto_id}", response_model=ExpenseResponse)
def get_expense(
    gasto_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    gasto = db.query(ExpenseDB).filter(ExpenseDB.id == gasto_id).first()

    if gasto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el gasto #{gasto_id}.",
        )

    return gasto


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Annotated[Session, Depends(get_db)],
):
    db_expense = ExpenseDB(
        empleado=expense.empleado,
        fecha=expense.fecha,
        concepto=expense.concepto,
        categoria=expense.categoria,
        importe=expense.importe,
        adjunto_url=expense.adjunto_url,
        estado="PENDIENTE_BAW",
    )

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # 1. Preparar el diccionario con los datos del gasto
    gasto_payload = {
        "id": db_expense.id,
        "empleado": db_expense.empleado,
        "fecha": db_expense.fecha.isoformat(),
        "concepto": db_expense.concepto,
        "categoria": db_expense.categoria,
        "importe": float(db_expense.importe),
    }

    # 2. Invocar a BAW e intentar guardar el ID de instancia recibido
    try:
        instance_id = start_baw_instance(gasto_payload)
        if instance_id:
            db_expense.baw_instance_id = instance_id
            db.commit()
            db.refresh(db_expense)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "No se pudo iniciar el proceso en BAW para el gasto %s: %s",
            db_expense.id,
            exc,
        )

    return db_expense
