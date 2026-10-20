import asyncio
import logging
import os
import ssl
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 10.0

BAW_INSTANCES_PATH = "/rest/bpm/wle/v1/processes/search"
APPIAN_INSTANCES_PATH = "/suite/webapi/expensr/listActiveInstances"


class ProcessInstance(BaseModel):
    id: str
    sistema: str
    etapa_actual: str
    horas_en_etapa: float | None = None
    prioridad: str = "Normal"


class SourceResult(BaseModel):
    sistema: str
    configurado: bool
    ok: bool
    instancias: list[ProcessInstance] = []
    error: str | None = None


def _no_configurado(sistema: str) -> SourceResult:
    return SourceResult(
        sistema=sistema,
        configurado=False,
        ok=False,
        instancias=[],
        error=f"{sistema} no está configurado.",
    )


def _no_disponible(sistema: str) -> SourceResult:
    return SourceResult(
        sistema=sistema,
        configurado=True,
        ok=False,
        instancias=[],
        error=f"{sistema} no responde o devolvió una respuesta inesperada.",
    )


def _parse_baw(data: Any) -> list[ProcessInstance]:
    """Convierte la respuesta de búsqueda de instancias de BAW."""
    if isinstance(data, dict):
        contenido = data.get("data", {})
        if not isinstance(contenido, dict):
            raise TypeError("Formato inesperado en la respuesta de BAW")

        items = contenido.get("processes", [])
    elif isinstance(data, list):
        items = data
    else:
        raise TypeError("Formato inesperado en la respuesta de BAW")

    if not isinstance(items, list):
        raise TypeError("La lista de instancias de BAW no es válida")

    instancias = []

    for item in items:
        if not isinstance(item, dict):
            continue

        identificador = item.get("piid") or item.get("id")
        if identificador is None:
            continue

        estado = item.get("executionState") or item.get("state") or "En curso"

        instancias.append(
            ProcessInstance(
                id=str(identificador),
                sistema="BAW",
                etapa_actual=str(estado),
                horas_en_etapa=None,
                prioridad="Normal",
            )
        )

    return instancias


def _parse_appian(data: Any) -> list[ProcessInstance]:
    """Convierte la respuesta de instancias de Appian."""
    if not isinstance(data, list):
        raise TypeError("Formato inesperado en la respuesta de Appian")

    return [
        ProcessInstance(
            id=str(item["id"]),
            sistema="Appian",
            etapa_actual=str(item["etapa_actual"]),
            horas_en_etapa=item.get("horas_en_etapa"),
            prioridad=item.get("prioridad", "Normal"),
        )
        for item in data
    ]


async def _fetch_baw(client: httpx.AsyncClient) -> SourceResult:
    base = os.getenv("BAW_BASE_URL", "").rstrip("/")
    user = os.getenv("BAW_USER", "")
    password = os.getenv("BAW_PASSWORD", "")

    if not (base and user and password):
        return _no_configurado("BAW")

    try:
        response = await client.get(
            f"{base}{BAW_INSTANCES_PATH}",
            auth=(user, password),
        )
        response.raise_for_status()
        instancias = _parse_baw(response.json())
    except (
        httpx.HTTPError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ) as exc:
        logger.warning("BAW no disponible: %s", exc)
        return _no_disponible("BAW")

    return SourceResult(
        sistema="BAW",
        configurado=True,
        ok=True,
        instancias=instancias,
    )


async def _fetch_appian(client: httpx.AsyncClient) -> SourceResult:
    base = os.getenv("APPIAN_BASE_URL", "").rstrip("/")
    api_key = os.getenv("APPIAN_API_KEY", "")

    if not (base and api_key):
        return _no_configurado("Appian")

    try:
        response = await client.get(
            f"{base}{APPIAN_INSTANCES_PATH}",
            headers={"Appian-API-Key": api_key},
        )
        response.raise_for_status()
        instancias = _parse_appian(response.json())
    except (
        httpx.HTTPError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ) as exc:
        logger.warning("Appian no disponible: %s", exc)
        return _no_disponible("Appian")

    return SourceResult(
        sistema="Appian",
        configurado=True,
        ok=True,
        instancias=instancias,
    )


def _baw_ssl_context() -> ssl.SSLContext | bool:
    ruta = os.getenv("BAW_CA_BUNDLE", "").strip()

    if not ruta:
        return True

    if not Path(ruta).is_file():
        logger.warning(
            "BAW_CA_BUNDLE no apunta a un archivo válido; "
            "se usará la verificación SSL predeterminada."
        )
        return True

    context = ssl.create_default_context(cafile=ruta)
    permitir_legacy = os.getenv("BAW_ALLOW_LEGACY_CERTS", "").strip().lower()

    if permitir_legacy in {"1", "true", "yes", "si", "sí"}:
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT
            logger.warning(
                "BAW: compatibilidad temporal con certificados legacy activada."
            )
        else:
            logger.warning(
                "BAW: esta versión de Python no permite modificar VERIFY_X509_STRICT."
            )

    return context


async def fetch_all() -> list[SourceResult]:
    """Consulta BAW y Appian en paralelo. Nunca lanza excepción."""
    async with (
        httpx.AsyncClient(
            timeout=TIMEOUT_SEGUNDOS,
            verify=_baw_ssl_context(),
        ) as baw_client,
        httpx.AsyncClient(timeout=TIMEOUT_SEGUNDOS) as appian_client,
    ):
        resultados = await asyncio.gather(
            _fetch_baw(baw_client),
            _fetch_appian(appian_client),
        )

    return list(resultados)
