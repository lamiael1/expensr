from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.routers import chat


def test_chat_devuelve_respuesta_de_gemini(client: TestClient, monkeypatch):
    """El endpoint devuelve la respuesta de Gemini cuando no llama a herramientas."""
    respuesta = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(parts=[SimpleNamespace(function_call=None)])
            )
        ],
        text="Hola, puedo ayudarte con tus gastos.",
    )

    monkeypatch.setattr(
        chat,
        "_generate",
        lambda *args, **kwargs: (respuesta, "modelo-test"),
    )

    response = client.post(
        "/chat/",
        json={"message": "Hola", "empleado": "empleado_007"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Hola, puedo ayudarte con tus gastos.",
        "function_called": None,
    }


def test_chat_ejecuta_herramienta_con_empleado_recibido(
    client: TestClient, monkeypatch
):
    """La herramienta recibe el empleado del request, no uno elegido por Gemini."""
    llamada = SimpleNamespace(name="listar_gastos", args={"empleado": "empleado_099"})
    primera_respuesta = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(parts=[SimpleNamespace(function_call=llamada)])
            )
        ],
        text=None,
    )
    segunda_respuesta = SimpleNamespace(
        candidates=[],
        text="Tienes dos gastos registrados.",
    )

    llamadas_generate = iter(
        [
            (primera_respuesta, "modelo-test"),
            (segunda_respuesta, "modelo-test"),
        ]
    )
    monkeypatch.setattr(
        chat,
        "_generate",
        lambda *args, **kwargs: next(llamadas_generate),
    )

    argumentos_recibidos = {}

    def herramienta_falsa(*, db, empleado, mes=None, categoria=None):
        argumentos_recibidos.update(
            empleado=empleado,
            mes=mes,
            categoria=categoria,
            db=db,
        )
        return {"total": 2, "gastos": []}

    monkeypatch.setitem(
        chat.FUNCTION_IMPLEMENTATIONS,
        "listar_gastos",
        herramienta_falsa,
    )

    response = client.post(
        "/chat/",
        json={"message": "Lista mis gastos", "empleado": "empleado_007"},
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Tienes dos gastos registrados."
    assert response.json()["function_called"] == "listar_gastos"
    assert argumentos_recibidos["empleado"] == "empleado_007"
    assert argumentos_recibidos["db"] is not None
