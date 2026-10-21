from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expense_db import ExpenseDB
from app.services.process_sources import ProcessInstance, fetch_all

router = APIRouter(prefix="/monitor", tags=["Monitor"])

SLA_HORAS = 48  # un gasto cumple el SLA si se resuelve en 48 h o menos
DIAS_SERIE = 7


class ExpenseInstance(BaseModel):
    id: int
    empleado: str
    concepto: str
    importe: float
    sistema: str
    etapa_actual: str
    prioridad: str
    estado: str
    fecha_creacion: str
    horas_en_etapa: float | None = None


class SerieTiempo(BaseModel):
    dia: str
    baw_horas: float
    appian_horas: float


class FuenteEstado(BaseModel):
    sistema: str
    configurado: bool
    ok: bool
    error: str | None = None


class KPIOverview(BaseModel):
    total_expenses: int
    total_amount: float
    pending_baw: int
    pending_appian: int
    approved: int
    rejected: int
    completados_hoy: int
    en_curso: int
    tiempo_medio_horas: float | None = None
    sla_pct: float | None = None
    series_tiempos: list[SerieTiempo]
    instancias: list[ExpenseInstance]
    fuentes: list[FuenteEstado] = []
    avisos: list[str] = []
    instancias_externas: list[ProcessInstance] = []


def _aware(valor: datetime | None) -> datetime | None:
    """SQLite devuelve fechas sin zona horaria; las tratamos como UTC."""
    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=UTC)
    return valor


def _horas(inicio: datetime | None, fin: datetime | None) -> float | None:
    inicio, fin = _aware(inicio), _aware(fin)
    if inicio is None or fin is None:
        return None
    return (fin - inicio).total_seconds() / 3600


def _media(valores: list[float]) -> float:
    return round(sum(valores) / len(valores), 1) if valores else 0.0


def _series_tiempos(db: Session, ahora: datetime) -> list[SerieTiempo]:
    desde = (ahora - timedelta(days=DIAS_SERIE - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    por_dia: dict = {}
    for i in range(DIAS_SERIE):
        dia = (desde + timedelta(days=i)).date()
        por_dia[dia] = {"baw": [], "appian": []}

    gastos = db.query(ExpenseDB).filter(ExpenseDB.fecha_creacion >= desde).all()

    for gasto in gastos:
        dia = _aware(gasto.fecha_creacion).date()
        if dia not in por_dia:
            continue

        horas_baw = _horas(gasto.fecha_creacion, gasto.fecha_validacion_baw)
        horas_appian = _horas(gasto.fecha_validacion_baw, gasto.fecha_decision_appian)

        if horas_baw is not None:
            por_dia[dia]["baw"].append(horas_baw)
        if horas_appian is not None:
            por_dia[dia]["appian"].append(horas_appian)

    return [
        SerieTiempo(
            dia=dia.isoformat(),
            baw_horas=_media(valores["baw"]),
            appian_horas=_media(valores["appian"]),
        )
        for dia, valores in por_dia.items()
    ]


@router.get("/overview", response_model=KPIOverview)
async def get_monitor_overview(
    db: Annotated[Session, Depends(get_db)],
):
    ahora = datetime.now(UTC)

    # BAW y Appian se consultan en paralelo; nunca lanza excepción.
    fuentes = await fetch_all()

    totals = db.query(
        func.count(ExpenseDB.id),
        func.coalesce(func.sum(ExpenseDB.importe), 0),
    ).one()

    pending_baw = (
        db.query(func.count(ExpenseDB.id))
        .filter(ExpenseDB.estado == "PENDIENTE_BAW")
        .scalar()
        or 0
    )

    pending_appian = (
        db.query(func.count(ExpenseDB.id))
        .filter(ExpenseDB.estado == "PENDIENTE_APPIAN")
        .scalar()
        or 0
    )

    approved = (
        db.query(func.count(ExpenseDB.id))
        .filter(ExpenseDB.estado.in_(["APROBADO", "APROBADO_BAW"]))
        .scalar()
        or 0
    )

    rejected = (
        db.query(func.count(ExpenseDB.id))
        .filter(ExpenseDB.estado.in_(["RECHAZADO", "RECHAZADO_BAW"]))
        .scalar()
        or 0
    )

    today = ahora.date()

    completados_hoy = (
        db.query(func.count(ExpenseDB.id))
        .filter(
            func.date(ExpenseDB.fecha_decision_appian) == today,
            ExpenseDB.decision_final.is_not(None),
        )
        .scalar()
        or 0
    )

    # Tiempo medio y SLA, sobre los gastos con decisión final de Appian
    resueltos = (
        db.query(ExpenseDB).filter(ExpenseDB.fecha_decision_appian.is_not(None)).all()
    )
    duraciones = [
        horas
        for gasto in resueltos
        if (horas := _horas(gasto.fecha_creacion, gasto.fecha_decision_appian))
        is not None
    ]

    tiempo_medio_horas = _media(duraciones) if duraciones else None
    sla_pct = (
        round(100 * sum(1 for h in duraciones if h <= SLA_HORAS) / len(duraciones), 1)
        if duraciones
        else None
    )

    expenses = (
        db.query(ExpenseDB).order_by(ExpenseDB.fecha_creacion.desc()).limit(100).all()
    )

    instancias = []

    for expense in expenses:
        estado = expense.estado or "SIN_ESTADO"
        horas_en_etapa = None

        if estado == "PENDIENTE_BAW":
            sistema = "BAW"
            etapa = "Pendiente de validación BAW"
            horas_en_etapa = _horas(expense.fecha_creacion, ahora)
        elif estado == "PENDIENTE_APPIAN":
            sistema = "Appian"
            etapa = "Pendiente de decisión financiera"
            horas_en_etapa = _horas(
                expense.fecha_validacion_baw or expense.fecha_creacion, ahora
            )
        elif estado in (
            "APROBADO",
            "RECHAZADO",
            "APROBADO_BAW",
            "RECHAZADO_BAW",
        ):
            sistema = "Finalizado"
            etapa = "Proceso finalizado"
        else:
            sistema = "Expensr"
            etapa = estado.replace("_", " ").capitalize()

        instancias.append(
            ExpenseInstance(
                id=expense.id,
                empleado=expense.empleado,
                concepto=expense.concepto,
                importe=float(expense.importe),
                sistema=sistema,
                etapa_actual=etapa,
                prioridad=("Alta" if expense.requiere_revision_manager else "Normal"),
                estado=estado,
                fecha_creacion=(
                    expense.fecha_creacion.isoformat() if expense.fecha_creacion else ""
                ),
                horas_en_etapa=(
                    round(horas_en_etapa, 1) if horas_en_etapa is not None else None
                ),
            )
        )

    return KPIOverview(
        total_expenses=totals[0],
        total_amount=float(totals[1]),
        pending_baw=pending_baw,
        pending_appian=pending_appian,
        approved=approved,
        rejected=rejected,
        completados_hoy=completados_hoy,
        en_curso=pending_baw + pending_appian,
        tiempo_medio_horas=tiempo_medio_horas,
        sla_pct=sla_pct,
        series_tiempos=_series_tiempos(db, ahora),
        instancias=instancias,
        fuentes=[
            FuenteEstado(
                sistema=f.sistema,
                configurado=f.configurado,
                ok=f.ok,
                error=f.error,
            )
            for f in fuentes
        ],
        avisos=[f.error for f in fuentes if not f.ok and f.error],
        instancias_externas=[i for f in fuentes if f.ok for i in f.instancias],
    )
