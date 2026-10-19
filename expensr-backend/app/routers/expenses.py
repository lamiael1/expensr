from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense import ExpenseCreate, ExpenseResponse
from app.models.expense_db import ExpenseDB

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/", response_model=list[ExpenseResponse])
def get_expenses(db: Annotated[Session, Depends(get_db)]):
    return db.query(ExpenseDB).order_by(ExpenseDB.fecha_creacion.desc()).all()


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

    return db_expense
