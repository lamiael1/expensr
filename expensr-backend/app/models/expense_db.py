from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.db.database import Base


class ExpenseDB(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    empleado = Column(String(100), nullable=False)
    fecha = Column(Date, nullable=False)
    concepto = Column(String(255), nullable=False)
    categoria = Column(String(100), nullable=False)
    importe = Column(Numeric(10, 2), nullable=False)
    adjunto_url = Column(Text, nullable=True)

    # Campos gestionados por IBM BAW
    centro_coste = Column(String(100), nullable=True)
    requiere_revision_manager = Column(Boolean, nullable=False, default=False)
    estado = Column(String(50), nullable=False, default="PENDIENTE_BAW")
    comentario_baw = Column(Text, nullable=True)
    fecha_validacion_baw = Column(DateTime(timezone=True), nullable=True)

    # Campos gestionados por Appian
    acumulado_mes = Column(Numeric(10, 2), nullable=True)
    presupuesto_restante = Column(Numeric(10, 2), nullable=True)
    decision_final = Column(String(50), nullable=True)
    comentario_appian = Column(Text, nullable=True)
    fecha_decision_appian = Column(DateTime(timezone=True), nullable=True)

    # Trazabilidad
    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
