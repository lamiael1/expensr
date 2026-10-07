from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ExpenseCreate(BaseModel):
    empleado: str
    fecha: date
    concepto: str
    categoria: str
    importe: float
    adjunto_url: str | None = None


class ExpenseResponse(BaseModel):
    id: int
    empleado: str
    fecha: date
    concepto: str
    categoria: str
    importe: float
    adjunto_url: str | None = None

    centro_coste: str | None = None
    requiere_revision_manager: bool
    estado: str
    comentario_baw: str | None = None
    fecha_validacion_baw: datetime | None = None

    acumulado_mes: float | None = None
    presupuesto_restante: float | None = None
    decision_final: str | None = None
    comentario_appian: str | None = None
    fecha_decision_appian: datetime | None = None

    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
