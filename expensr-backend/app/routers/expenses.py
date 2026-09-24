from fastapi import APIRouter, File, UploadFile
from app.models.expense import ExpenseCreate, ExpenseResponse

router = APIRouter(prefix="/expenses", tags=["Expenses"])

fake_expenses = [
    {
        "id": 1,
        "fecha": "2026-03-20",
        "categoria": "Transporte",
        "importe": 15.50,
    },
    {
        "id": 2,
        "fecha": "2026-03-21",
        "categoria": "Restauración",
        "importe": 42.00,
    },
    {
        "id": 3,
        "fecha": "2026-03-22",
        "categoria": "Material Oficina",
        "importe": 89.99,
    },
]


@router.get("/", response_model=list[ExpenseResponse])
def get_expenses():
    return fake_expenses


@router.post("/", response_model=ExpenseResponse, status_code=201)
def create_expense(expense: ExpenseCreate):
    new_id = len(fake_expenses) + 1 if fake_expenses else 1
    new_expense = {
        "id": new_id,
        "fecha": expense.fecha,
        "categoria": expense.categoria,
        "importe": expense.importe,
    }
    fake_expenses.append(new_expense)
    return new_expense


# Endpoint para subir el archivo de la factura
@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    # Simulación de extracción de datos (posteriormente se integrará IA / OCR)
    new_id = len(fake_expenses) + 1 if fake_expenses else 1
    extracted_expense = {
        "id": new_id,
        "fecha": "2026-03-23",
        "categoria": "Procesado por Factura",
        "importe": 120.50,
    }

    fake_expenses.append(extracted_expense)

    return {
        "message": f"Archivo '{file.filename}' recibido y procesado con éxito",
        "expense": extracted_expense,
    }
