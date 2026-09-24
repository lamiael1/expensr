from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.db.database import Base


class ExpenseDB(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    concepto = Column(String, index=True)
    categoria = Column(String)
    importe = Column(Float)
    estado = Column(String, default="PENDIENTE_BAW")

    # Timestamps para la trazabilidad solicitada en el proyecto
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_validacion_baw = Column(DateTime, nullable=True)
    fecha_decision_appian = Column(DateTime, nullable=True)
