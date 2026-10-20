from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ExpenseDB(Base):
    __tablename__ = "gastos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    empleado: Mapped[str] = mapped_column(String(100))
    fecha: Mapped[date] = mapped_column(Date)
    concepto: Mapped[str] = mapped_column(String(255))
    categoria: Mapped[str] = mapped_column(String(100))
    importe: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    adjunto_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Campos gestionados por IBM BAW
    centro_coste: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requiere_revision_manager: Mapped[bool] = mapped_column(Boolean, default=False)
    estado: Mapped[str] = mapped_column(String(50), default="PENDIENTE_BAW")
    comentario_baw: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_validacion_baw: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Campos gestionados por Appian
    acumulado_mes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    presupuesto_restante: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    decision_final: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comentario_appian: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_decision_appian: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Trazabilidad
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
