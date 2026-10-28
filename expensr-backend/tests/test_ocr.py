from datetime import date

import pytest

from app.routers import ocr
from app.services.invoice_ocr import ExtractedInvoice, InvoiceExtractionError


@pytest.mark.parametrize(
    "mime_type",
    [
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    ],
)
def test_extract_invoice_acepta_formatos_permitidos(client, monkeypatch, mime_type):
    factura = ExtractedInvoice(
        fecha=date(2026, 10, 28),
        importe=50.0,
        categoria="Dietas",
        concepto="Comida de trabajo",
    )
    llamada = {}

    def extraer_contenido(file_bytes, content_type):
        llamada["file_bytes"] = file_bytes
        llamada["mime_type"] = content_type
        return factura

    monkeypatch.setattr(ocr, "extract_invoice_data", extraer_contenido)

    response = client.post(
        "/extract-invoice",
        files={"file": ("factura", b"contenido de prueba", mime_type)},
    )

    assert response.status_code == 200
    assert response.json() == {
        "fecha": "2026-10-28",
        "importe": 50.0,
        "categoria": "Dietas",
        "concepto": "Comida de trabajo",
    }
    assert llamada == {
        "file_bytes": b"contenido de prueba",
        "mime_type": mime_type,
    }


def test_extract_invoice_rechaza_formato_no_permitido(client):
    response = client.post(
        "/extract-invoice",
        files={"file": ("factura.txt", b"texto", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == (
        "Formato no soportado. Usa JPG, PNG, WEBP o PDF."
    )


def test_extract_invoice_rechaza_archivo_mayor_de_10_mb(client):
    contenido = b"x" * (ocr.MAX_FILE_SIZE_BYTES + 1)

    response = client.post(
        "/extract-invoice",
        files={"file": ("factura.pdf", contenido, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == ("El archivo supera el tamaño máximo de 10 MB.")


def test_extract_invoice_devuelve_502_si_falla_la_extraccion(
    client,
    monkeypatch,
):
    def fallar_extraccion(file_bytes, mime_type):
        raise InvoiceExtractionError("No se pudo leer la factura.")

    monkeypatch.setattr(ocr, "extract_invoice_data", fallar_extraccion)

    response = client.post(
        "/extract-invoice",
        files={"file": ("factura.pdf", b"contenido", "application/pdf")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "No se pudo leer la factura."
