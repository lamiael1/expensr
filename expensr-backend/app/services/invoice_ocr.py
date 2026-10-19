import json
import logging
from datetime import date

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

client = genai.Client()
MODEL = "gemini-3.8-flash"

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

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                "Extrae los datos de este documento.",
            ],
            config=config,
        )
    except APIError as exc:
        logger.exception("Error llamando a Gemini Vision para OCR de factura")
        raise InvoiceExtractionError(
            "No se pudo contactar con el servicio de IA."
        ) from exc

    raw_text = response.text
    if not raw_text:
        raise InvoiceExtractionError("El modelo no devolvió ningún dato.")

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
