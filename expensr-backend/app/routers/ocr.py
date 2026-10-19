from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.invoice_ocr import (
    ExtractedInvoice,
    InvoiceExtractionError,
    extract_invoice_data,
)

router = APIRouter(tags=["OCR"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/extract-invoice", response_model=ExtractedInvoice)
async def extract_invoice(file: Annotated[UploadFile, File()]):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato no soportado. Usa JPG, PNG, WEBP o PDF.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el tamaño máximo de 10 MB.",
        )

    try:
        return extract_invoice_data(file_bytes, file.content_type)
    except InvoiceExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
