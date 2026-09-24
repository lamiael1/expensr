from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense import ExpenseCreate, ExpenseResponse
from app.models.expense_db import ExpenseDB

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/", response_model=list[ExpenseResponse])
def get_expenses(db: Annotated[Session, Depends(get_db)]):
    return db.query(ExpenseDB).all()


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate, db: Annotated[Session, Depends(get_db)]
):
    db_expense = ExpenseDB(
        concepto=expense.concepto,
        categoria=expense.categoria,
        importe=expense.importe,
        estado="PENDIENTE_BAW",
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.post("/upload", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
):
    # Simulación de extracción por factura (se guardará la ruta/bucket en la fase de IA)
    extracted_expense = ExpenseDB(
        concepto=f"Factura: {file.filename}",
        categoria="Procesado por Factura",
        importe=120.50,
        estado="PENDIENTE_BAW",
    )
    db.add(extracted_expense)
    db.commit()
    db.refresh(extracted_expense)
    return extracted_expense
