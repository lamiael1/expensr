from pydantic import BaseModel


# Modelo para recibir datos al crear un gasto
class ExpenseCreate(BaseModel):
    fecha: str
    categoria: str
    importe: float


# Modelo para devolver datos al consultar (incluye ID)
class ExpenseResponse(ExpenseCreate):
    id: int
