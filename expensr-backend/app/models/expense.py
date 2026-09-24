from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExpenseCreate(BaseModel):
    concepto: str
    categoria: str
    importe: float


class ExpenseResponse(BaseModel):
    id: int
    concepto: str
    categoria: str
    importe: float
    estado: str
    fecha_creacion: datetime
    fecha_validacion_baw: datetime | None = None
    fecha_decision_appian: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
