import asyncio

import httpx

from app.services import process_sources as ps


def _cliente(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def _llamar(fetch, handler):
    async with _cliente(handler) as client:
        return await fetch(client)


def test_baw_no_configurado():
    resultado = asyncio.run(_llamar(ps._fetch_baw, lambda request: httpx.Response(200)))

    assert resultado.configurado is False
    assert resultado.ok is False
    assert resultado.error == "BAW no está configurado."


def test_appian_no_configurado():
    resultado = asyncio.run(
        _llamar(ps._fetch_appian, lambda request: httpx.Response(200))
    )

    assert resultado.configurado is False
    assert resultado.ok is False


def test_appian_ok_devuelve_instancias(monkeypatch):
    monkeypatch.setenv("APPIAN_BASE_URL", "http://appian.test")
    monkeypatch.setenv("APPIAN_API_KEY", "clave-de-prueba")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Appian-API-Key"] == "clave-de-prueba"
        return httpx.Response(
            200,
            json=[
                {
                    "c3": "2411",
                    "c4": "",
                    "c2": "2026-10-28T10:00:00Z",
                }
            ],
        )

    resultado = asyncio.run(_llamar(ps._fetch_appian, handler))

    assert resultado.ok is True
    assert resultado.instancias[0].id == "2411"
    assert resultado.instancias[0].sistema == "Appian"
    assert resultado.instancias[0].etapa_actual == "Pendiente de decisión Finanzas"


def test_baw_error_http_no_lanza_excepcion(monkeypatch):
    monkeypatch.setenv("BAW_BASE_URL", "http://baw.test")
    monkeypatch.setenv("BAW_USER", "usuario")
    monkeypatch.setenv("BAW_PASSWORD", "clave")

    resultado = asyncio.run(_llamar(ps._fetch_baw, lambda request: httpx.Response(500)))

    assert resultado.configurado is True
    assert resultado.ok is False
    assert "no responde" in resultado.error


def test_appian_caido_no_lanza_excepcion(monkeypatch):
    monkeypatch.setenv("APPIAN_BASE_URL", "http://appian.test")
    monkeypatch.setenv("APPIAN_API_KEY", "clave")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin conexión")

    resultado = asyncio.run(_llamar(ps._fetch_appian, handler))

    assert resultado.configurado is True
    assert resultado.ok is False


def test_overview_sigue_funcionando_si_baw_cae(client, monkeypatch):
    async def fake_fetch_all():
        return [
            ps.SourceResult(
                sistema="BAW",
                configurado=True,
                ok=False,
                error="BAW no responde o devolvió una respuesta inesperada.",
            ),
            ps.SourceResult(
                sistema="Appian",
                configurado=True,
                ok=True,
                instancias=[
                    ps.ProcessInstance(
                        id="G-1", sistema="Appian", etapa_actual="Decisión"
                    )
                ],
            ),
        ]

    monkeypatch.setattr("app.routers.monitor.fetch_all", fake_fetch_all)

    response = client.get("/monitor/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["avisos"] == ["BAW no responde o devolvió una respuesta inesperada."]
    assert [i["id"] for i in body["instancias_externas"]] == ["G-1"]
    assert [f["ok"] for f in body["fuentes"]] == [False, True]


def test_overview_sin_credenciales_avisa_de_ambos(client):
    response = client.get("/monitor/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["avisos"] == ["BAW no está configurado.", "Appian no está configurado."]
    assert body["instancias_externas"] == []
