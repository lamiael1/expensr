from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/monitor", tags=["Monitor"])


class KPIOverview(BaseModel):
    total_expenses: int
    total_amount: float
    pending_baw: int
    pending_appian: int
    approved: int
    rejected: int


@router.get("/overview", response_model=KPIOverview)
async def get_monitor_overview():
    # Métricas simuladas (en la fase 3 se calcularán desde SQL/Base de datos)
    return KPIOverview(
        total_expenses=3,
        total_amount=147.49,
        pending_baw=1,
        pending_appian=1,
        approved=1,
        rejected=0,
    )
