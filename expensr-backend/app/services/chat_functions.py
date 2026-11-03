from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from google.genai import types
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expense_db import ExpenseDB

ZONA_HORARIA = ZoneInfo("Europe/Madrid")

DESCRIPCION_MES = "Mes del año (1-12). Si se indica sin año, se usa el año actual."
DESCRIPCION_ANIO = (
    "Año de los gastos. Si se indica un mes y se omite el año, se usa el año actual."
)

FUNCTION_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "listar_gastos",
            "description": (
                "Lista los gastos del empleado autenticado, opcionalmente "
                "filtrados por mes, año y/o categoría. Para 'este mes', "
                "usa el mes y año actuales indicados en las instrucciones."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mes": {
                        "type": "integer",
                        "description": DESCRIPCION_MES,
                    },
                    "anio": {
                        "type": "integer",
                        "description": DESCRIPCION_ANIO,
                    },
                    "categoria": {
                        "type": "string",
                        "description": (
                            "Categoría del gasto (ej. Dietas, Transporte, "
                            "Material, Formacion)."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_estado",
            "description": (
                "Consulta el estado de un gasto concreto del empleado autenticado. "
                "Si no se indica gasto_id, devuelve el gasto más reciente "
                "que sigue pendiente."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "gasto_id": {
                        "type": "integer",
                        "description": "ID del gasto a consultar. Opcional.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tiempo_medio_aprobacion",
            "description": (
                "Calcula el tiempo medio, en días, que tardan en resolverse "
                "(aprobarse o rechazarse) los gastos del empleado autenticado."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def listar_gastos(
    db: Session,
    empleado: str,
    mes: int | None = None,
    anio: int | None = None,
    categoria: str | None = None,
) -> dict[str, Any]:
    query = db.query(ExpenseDB).filter(ExpenseDB.empleado == empleado)

    if mes is not None:
        query = query.filter(func.extract("month", ExpenseDB.fecha) == mes)

        if anio is None:
            anio = datetime.now(ZONA_HORARIA).year

    if anio is not None:
        query = query.filter(func.extract("year", ExpenseDB.fecha) == anio)

    if categoria is not None:
        query = query.filter(func.lower(ExpenseDB.categoria) == categoria.lower())

    gastos = query.order_by(ExpenseDB.fecha.desc()).limit(20).all()

    return {
        "total": len(gastos),
        "gastos": [
            {
                "id": gasto.id,
                "fecha": gasto.fecha.isoformat(),
                "concepto": gasto.concepto,
                "categoria": gasto.categoria,
                "importe": float(gasto.importe),
                "estado": gasto.estado,
            }
            for gasto in gastos
        ],
    }


def consultar_estado(
    db: Session,
    empleado: str,
    gasto_id: int | None = None,
) -> dict[str, Any]:
    query = db.query(ExpenseDB).filter(ExpenseDB.empleado == empleado)

    if gasto_id is not None:
        gasto = query.filter(ExpenseDB.id == gasto_id).first()
        if gasto is None:
            return {
                "encontrado": False,
                "mensaje": f"No existe el gasto #{gasto_id} para este empleado.",
            }
    else:
        gasto = (
            query.filter(ExpenseDB.decision_final.is_(None))
            .order_by(ExpenseDB.fecha_creacion.desc())
            .first()
        )
        if gasto is None:
            return {"encontrado": False, "mensaje": "No hay gastos pendientes."}

    return {
        "encontrado": True,
        "id": gasto.id,
        "concepto": gasto.concepto,
        "importe": float(gasto.importe),
        "estado": gasto.estado,
        "centro_coste": gasto.centro_coste,
        "requiere_revision_manager": gasto.requiere_revision_manager,
        "decision_final": gasto.decision_final,
    }


def tiempo_medio_aprobacion(db: Session, empleado: str) -> dict[str, Any]:
    gastos = (
        db.query(ExpenseDB)
        .filter(
            ExpenseDB.empleado == empleado,
            ExpenseDB.decision_final.is_not(None),
        )
        .all()
    )

    if not gastos:
        return {
            "muestras": 0,
            "tiempo_medio_dias": None,
            "mensaje": "Aún no hay gastos resueltos.",
        }

    dias = []
    for gasto in gastos:
        fin = gasto.fecha_decision_appian or gasto.fecha_validacion_baw
        if fin and gasto.fecha_creacion:
            dias.append((fin - gasto.fecha_creacion).total_seconds() / 86400)

    if not dias:
        return {
            "muestras": 0,
            "tiempo_medio_dias": None,
            "mensaje": "No hay timestamps suficientes.",
        }

    return {
        "muestras": len(dias),
        "tiempo_medio_dias": round(sum(dias) / len(dias), 2),
    }


FUNCTION_IMPLEMENTATIONS = {
    "listar_gastos": listar_gastos,
    "consultar_estado": consultar_estado,
    "tiempo_medio_aprobacion": tiempo_medio_aprobacion,
}


FUNCTION_DECLARATIONS_GEMINI = [
    types.FunctionDeclaration(
        name="listar_gastos",
        description=(
            "Lista los gastos del empleado autenticado, opcionalmente "
            "filtrados por mes, año y/o categoría. Para 'este mes', "
            "usa el mes y año actuales indicados en las instrucciones."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "mes": types.Schema(
                    type=types.Type.INTEGER,
                    description=DESCRIPCION_MES,
                ),
                "anio": types.Schema(
                    type=types.Type.INTEGER,
                    description=DESCRIPCION_ANIO,
                ),
                "categoria": types.Schema(
                    type=types.Type.STRING,
                    description=(
                        "Categoría del gasto (ej. Dietas, Transporte, "
                        "Material, Formacion)."
                    ),
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="consultar_estado",
        description=(
            "Consulta el estado de un gasto concreto del empleado autenticado. "
            "Si no se indica gasto_id, devuelve el gasto más reciente "
            "que sigue pendiente."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "gasto_id": types.Schema(
                    type=types.Type.INTEGER,
                    description="ID del gasto a consultar. Opcional.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="tiempo_medio_aprobacion",
        description=(
            "Calcula el tiempo medio, en días, que tardan en resolverse "
            "(aprobarse o rechazarse) los gastos del empleado autenticado."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
]

GEMINI_TOOLS = [types.Tool(function_declarations=FUNCTION_DECLARATIONS_GEMINI)]
