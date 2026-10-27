import json
import logging
from datetime import date

from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Configuración del cliente con timeout explícito de 20s y 1 solo intento
client = genai.Client(
    http_options=types.HttpOptions(
        timeout=20_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    )
)

# Lista de modelos con fallback
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-3.5-flash-lite"]
CATEGORIAS_VALIDAS = ["Dietas", "Transporte", "Material", "Formacion"]

OCR_SYSTEM_PROMPT = (
    "Eres un extractor de datos de facturas y tickets de gasto empresarial. "
    "Analiza la imagen o PDF adjunto y devuelve ÚNICAMENTE un JSON con estos "
    "campos: fecha (formato YYYY-MM-DD), importe (número, el importe total "
    "pagado, sin símbolo de moneda), categoria (una de: "
    f"{', '.join(CATEGORIAS_VALIDAS)}) y concepto (una descripción breve, "
    "en español, de qué es el gasto). "
    "Si algún dato no es legible o no aparece, usa null para ese campo. "
    "No incluyas explicaciones, solo el JSON."
)

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "fecha": types.Schema(type=types.Type.STRING, nullable=True),
        "importe": types.Schema(type=types.Type.NUMBER, nullable=True),
        "categoria": types.Schema(
            type=types.Type.STRING,
            enum=CATEGORIAS_VALIDAS,
            nullable=True,
        ),
        "concepto": types.Schema(type=types.Type.STRING, nullable=True),
    },
    required=["fecha", "importe", "categoria", "concepto"],
)


class ExtractedInvoice(BaseModel):
    fecha: date | None = None
    importe: float | None = None
    categoria: str | None = None
    concepto: str | None = None


class InvoiceExtractionError(Exception):
    """Fallo al extraer datos de la factura (API, parseo o validación)."""


def extract_invoice_data(file_bytes: bytes, mime_type: str) -> ExtractedInvoice:
    config = types.GenerateContentConfig(
        system_instruction=OCR_SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
    )

    response = None
    last_error = None

    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    "Extrae los datos de este documento.",
                ],
                config=config,
            )
            if response and response.text:
                break
        except (APIError, ServerError) as exc:
            logger.warning(
                "Modelo %s falló (%s). Probando siguiente...", model_name, exc
            )
            last_error = exc

    if not response or not response.text:
        raise InvoiceExtractionError(
            "El servicio de IA está experimentando alta latencia. Por favor, reintenta en unos segundos."
        ) from last_error

    raw_text = response.text

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.warning("JSON malformado del modelo: %s", raw_text)
        raise InvoiceExtractionError("El modelo devolvió un formato inválido.") from exc

    try:
        return ExtractedInvoice.model_validate(data)
    except ValidationError as exc:
        logger.warning("Datos extraídos no válidos: %s", data)
        raise InvoiceExtractionError("Los datos extraídos no son válidos.") from exc
