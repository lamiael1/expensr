import asyncio
from types import SimpleNamespace

import httpx
import pytest

from app.services import process_sources as ps


def ejecutar_fetch(fetch, handler):
    async def ejecutar():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch(client)

    return asyncio.run(ejecutar())


def test_parse_baw_procesa_respuesta_anidada_y_omite_filas_invalidas():
    datos = {
        "data": {
            "processes": [
                {"piid": 101, "executionState": "Active"},
                {"id": 102, "state": "Completed"},
                {"id": 103},
                {"nombre": "sin identificador"},
                "fila incorrecta",
            ]
        }
    }

    resultado = ps._parse_baw(datos)

    assert [(i.id, i.etapa_actual) for i in resultado] == [
        ("101", "Active"),
        ("102", "Completed"),
        ("103", "En curso"),
    ]


def test_parse_baw_acepta_lista_plana():
    resultado = ps._parse_baw([{"id": 55, "state": "Running"}])

    assert len(resultado) == 1
    assert resultado[0].id == "55"
    assert resultado[0].sistema == "BAW"
    assert resultado[0].etapa_actual == "Running"


@pytest.mark.parametrize(
    "datos",
    [
        None,
        {"data": None},
        {"data": {"processes": "no es una lista"}},
    ],
)
def test_parse_baw_rechaza_respuestas_con_formato_invalido(datos):
    with pytest.raises(TypeError):
        ps._parse_baw(datos)


def test_parse_appian_usa_c6_y_valores_predeterminados():
    datos = [
        {"c6": 8700, "c4": "", "c5": None},
        {
            "id": "APP-2",
            "etapa_actual": "Decisión financiera",
            "prioridad": "Alta",
            "horas_en_etapa": 3.5,
        },
        {},
        "fila incorrecta",
    ]

    resultado = ps._parse_appian(datos)

    assert [(i.id, i.etapa_actual, i.prioridad) for i in resultado] == [
        ("8700", "Activo", "Normal"),
        ("APP-2", "Decisión financiera", "Alta"),
    ]
    assert resultado[1].horas_en_etapa == 3.5


def test_parse_appian_rechaza_respuesta_que_no_es_lista():
    with pytest.raises(TypeError, match="Formato inesperado"):
        ps._parse_appian({"c6": 8700})


def test_fetch_baw_correcto(monkeypatch):
    monkeypatch.setenv("BAW_BASE_URL", "https://baw.example.test")
    monkeypatch.setenv("BAW_USER", "usuario")
    monkeypatch.setenv("BAW_PASSWORD", "clave")

    def handler(request):
        assert request.url.path == ps.BAW_INSTANCES_PATH
        return httpx.Response(
            200,
            json={"data": {"processes": [{"piid": "BAW-1"}]}},
        )

    resultado = ejecutar_fetch(ps._fetch_baw, handler)

    assert resultado.configurado is True
    assert resultado.ok is True
    assert resultado.instancias[0].id == "BAW-1"


def test_fetch_baw_devuelve_no_disponible_si_json_es_invalido(monkeypatch):
    monkeypatch.setenv("BAW_BASE_URL", "https://baw.example.test")
    monkeypatch.setenv("BAW_USER", "usuario")
    monkeypatch.setenv("BAW_PASSWORD", "clave")

    resultado = ejecutar_fetch(
        ps._fetch_baw,
        lambda request: httpx.Response(200, content=b"no es json"),
    )

    assert resultado.configurado is True
    assert resultado.ok is False
    assert resultado.error == ("BAW no responde o devolvió una respuesta inesperada.")


def test_fetch_appian_devuelve_no_disponible_si_falla_http(monkeypatch):
    monkeypatch.setenv("APPIAN_BASE_URL", "https://appian.example.test")
    monkeypatch.setenv("APPIAN_API_KEY", "clave-de-prueba")

    resultado = ejecutar_fetch(
        ps._fetch_appian,
        lambda request: httpx.Response(403),
    )

    assert resultado.configurado is True
    assert resultado.ok is False
    assert resultado.instancias == []


def test_fetch_appian_devuelve_no_disponible_si_json_es_invalido(monkeypatch):
    monkeypatch.setenv("APPIAN_BASE_URL", "https://appian.example.test")
    monkeypatch.setenv("APPIAN_API_KEY", "clave-de-prueba")

    resultado = ejecutar_fetch(
        ps._fetch_appian,
        lambda request: httpx.Response(200, content=b"no es json"),
    )

    assert resultado.configurado is True
    assert resultado.ok is False


def test_baw_ssl_usa_verificacion_predeterminada_si_no_hay_bundle(monkeypatch):
    monkeypatch.delenv("BAW_CA_BUNDLE", raising=False)

    assert ps._baw_ssl_context() is True


def test_baw_ssl_usa_verificacion_predeterminada_si_bundle_no_existe(
    monkeypatch,
):
    monkeypatch.setenv("BAW_CA_BUNDLE", "/ruta/que/no/existe.pem")
    monkeypatch.setattr(ps.Path, "is_file", lambda self: False)

    assert ps._baw_ssl_context() is True


def test_baw_ssl_aplica_compatibilidad_legacy(monkeypatch):
    monkeypatch.setenv("BAW_CA_BUNDLE", "/ruta/ca.pem")
    monkeypatch.setenv("BAW_ALLOW_LEGACY_CERTS", "true")
    monkeypatch.setattr(ps.Path, "is_file", lambda self: True)
    monkeypatch.setattr(ps.ssl, "VERIFY_X509_STRICT", 1, raising=False)

    contexto = SimpleNamespace(verify_flags=1)
    monkeypatch.setattr(
        ps.ssl,
        "create_default_context",
        lambda cafile: contexto,
    )

    resultado = ps._baw_ssl_context()

    assert resultado is contexto
    assert contexto.verify_flags == 0


def test_fetch_all_devuelve_fuentes_no_configuradas():
    resultados = asyncio.run(ps.fetch_all())

    assert [r.sistema for r in resultados] == ["BAW", "Appian"]
    assert all(r.configurado is False for r in resultados)
    assert all(r.ok is False for r in resultados)


def test_ssl_legacy_avisa_si_python_no_tiene_verify_x509_strict(
    monkeypatch,
    tmp_path,
    caplog,
):
    import logging
    import ssl
    from types import SimpleNamespace

    from app.services import process_sources

    ca_bundle = tmp_path / "ca.pem"
    ca_bundle.write_text("certificado de prueba")

    contexto_falso = SimpleNamespace(verify_flags=0)

    monkeypatch.setenv("BAW_CA_BUNDLE", str(ca_bundle))
    monkeypatch.setenv("BAW_ALLOW_LEGACY_CERTS", "true")
    monkeypatch.delattr(ssl, "VERIFY_X509_STRICT", raising=False)
    monkeypatch.setattr(
        ssl,
        "create_default_context",
        lambda cafile: contexto_falso,
    )

    with caplog.at_level(logging.WARNING):
        contexto = process_sources._baw_ssl_context()

    assert contexto is contexto_falso
    assert (
        "BAW: esta versión de Python no permite modificar VERIFY_X509_STRICT."
        in caplog.text
    )
