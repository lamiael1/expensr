import json
from datetime import date
from types import SimpleNamespace

import pytest

from app.services import invoice_ocr


def respuesta_gemini(texto):
    return SimpleNamespace(text=texto)


def reemplazar_generacion(monkeypatch, respuesta):
    def generar_contenido(**kwargs):
        return respuesta

    monkeypatch.setattr(
        invoice_ocr.client.models,
        "generate_content",
        generar_contenido,
    )


def test_extract_invoice_data_convierte_respuesta_valida(monkeypatch):
    datos = {
        "fecha": "2026-10-28",
        "importe": 50.25,
        "categoria": "Dietas",
        "concepto": "Comida de trabajo",
    }
    reemplazar_generacion(monkeypatch, respuesta_gemini(json.dumps(datos)))

    resultado = invoice_ocr.extract_invoice_data(b"imagen", "image/png")

    assert resultado.fecha == date(2026, 10, 28)
    assert resultado.importe == 50.25
    assert resultado.categoria == "Dietas"
    assert resultado.concepto == "Comida de trabajo"


@pytest.mark.parametrize(
    "respuesta",
    [
        None,
        respuesta_gemini(""),
    ],
)
def test_extract_invoice_data_falla_si_gemini_no_devuelve_texto(
    monkeypatch,
    respuesta,
):
    reemplazar_generacion(monkeypatch, respuesta)

    with pytest.raises(
        invoice_ocr.InvoiceExtractionError,
        match="Gemini no devolvió datos",
    ):
        invoice_ocr.extract_invoice_data(b"imagen", "image/png")


def test_extract_invoice_data_falla_si_json_es_invalido(monkeypatch):
    reemplazar_generacion(monkeypatch, respuesta_gemini("{json incorrecto"))

    with pytest.raises(
        invoice_ocr.InvoiceExtractionError,
        match="formato inválido",
    ):
        invoice_ocr.extract_invoice_data(b"imagen", "image/png")


def test_extract_invoice_data_falla_si_datos_no_validan(monkeypatch):
    datos = {
        "fecha": "fecha-incorrecta",
        "importe": "importe-incorrecto",
        "categoria": "Dietas",
        "concepto": "Comida de trabajo",
    }
    reemplazar_generacion(monkeypatch, respuesta_gemini(json.dumps(datos)))

    with pytest.raises(
        invoice_ocr.InvoiceExtractionError,
        match="no son válidos",
    ):
        invoice_ocr.extract_invoice_data(b"imagen", "image/png")


def test_extract_invoice_data_convierte_error_de_api(monkeypatch):
    class ErrorApiFalso(Exception):
        pass

    monkeypatch.setattr(invoice_ocr, "APIError", ErrorApiFalso)

    def fallar_generacion(**kwargs):
        raise ErrorApiFalso("servicio temporalmente no disponible")

    monkeypatch.setattr(
        invoice_ocr.client.models,
        "generate_content",
        fallar_generacion,
    )

    with pytest.raises(
        invoice_ocr.InvoiceExtractionError,
        match="Gemini no pudo procesar la factura",
    ):
        invoice_ocr.extract_invoice_data(b"imagen", "image/png")
