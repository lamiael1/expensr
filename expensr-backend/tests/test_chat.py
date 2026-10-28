from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.routers import chat


def crear_respuesta(texto, function_call=None):
    candidatos = []

    if function_call is not None:
        parte = SimpleNamespace(function_call=function_call)
        contenido = SimpleNamespace(parts=[parte])
        candidatos.append(SimpleNamespace(content=contenido))

    return SimpleNamespace(candidates=candidatos, text=texto)


def test_chat_devuelve_respuesta_de_gemini(client: TestClient, monkeypatch):
    """Devuelve el texto de Gemini cuando no solicita ejecutar una función."""
    respuesta = crear_respuesta("Hola, puedo ayudarte con tus gastos.")

    monkeypatch.setattr(
        chat,
        "_generate",
        lambda *args, **kwargs: (respuesta, "modelo-test"),
    )

    response = client.post("/chat/", json={"message": "Hola"})

    assert response.status_code == 200
    assert response.json() == {
        "response": "Hola, puedo ayudarte con tus gastos.",
        "function_called": None,
    }


def test_chat_ejecuta_herramienta_con_empleado_configurado(
    client: TestClient,
    monkeypatch,
):
    """La herramienta usa el empleado configurado, no el indicado por Gemini."""
    llamada = SimpleNamespace(
        name="listar_gastos",
        args={"empleado": "empleado_no_autorizado"},
    )
    primera_respuesta = crear_respuesta(None, llamada)
    segunda_respuesta = crear_respuesta("Tienes dos gastos registrados.")

    respuestas = iter(
        [
            (primera_respuesta, "modelo-test"),
            (segunda_respuesta, "modelo-test"),
        ]
    )
    monkeypatch.setattr(
        chat,
        "_generate",
        lambda *args, **kwargs: next(respuestas),
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

    response = client.post("/chat/", json={"message": "Lista mis gastos"})

    assert response.status_code == 200
    assert response.json()["response"] == "Tienes dos gastos registrados."
    assert response.json()["function_called"] == "listar_gastos"
    assert argumentos_recibidos["empleado"] == chat.DEMO_EMPLOYEE
    assert argumentos_recibidos["db"] is not None


def test_chat_devuelve_texto_vacio_si_gemini_no_devuelve_candidatos(
    client: TestClient,
    monkeypatch,
):
    respuesta = SimpleNamespace(candidates=[], text=None)
    monkeypatch.setattr(
        chat,
        "_generate",
        lambda *args, **kwargs: (respuesta, "modelo-test"),
    )

    response = client.post("/chat/", json={"message": "Hola"})

    assert response.status_code == 200
    assert response.json() == {"response": "", "function_called": None}


def test_chat_devuelve_mensaje_amable_si_falla_primera_llamada(
    client: TestClient,
    monkeypatch,
):
    class ErrorApiFalso(Exception):
        pass

    monkeypatch.setattr(chat, "APIError", ErrorApiFalso)

    def fallar(*args, **kwargs):
        raise ErrorApiFalso("servicio no disponible")

    monkeypatch.setattr(chat, "_generate", fallar)

    response = client.post("/chat/", json={"message": "Hola"})

    assert response.status_code == 200
    assert response.json() == {
        "response": (
            "No he podido conectar con el asistente de IA. "
            "Inténtalo de nuevo en unos segundos."
        ),
        "function_called": None,
    }


def test_chat_ignora_llamada_a_funcion_sin_nombre(
    client: TestClient,
    monkeypatch,
):
    llamada = SimpleNamespace(name="", args={})
    respuesta = crear_respuesta("Respuesta normal", llamada)
    monkeypatch.setattr(
        chat,
        "_generate",
        lambda *args, **kwargs: (respuesta, "modelo-test"),
    )

    response = client.post("/chat/", json={"message": "Hola"})

    assert response.status_code == 200
    assert response.json() == {
        "response": "Respuesta normal",
        "function_called": None,
    }


def test_chat_responde_si_gemini_pide_funcion_desconocida(
    client: TestClient,
    monkeypatch,
):
    llamada = SimpleNamespace(name="funcion_inexistente", args={})
    primera_respuesta = crear_respuesta(None, llamada)
    segunda_respuesta = crear_respuesta("No encontré esa operación.")

    respuestas = iter(
        [
            (primera_respuesta, "modelo-test"),
            (segunda_respuesta, "modelo-test"),
        ]
    )
    monkeypatch.setattr(
        chat,
        "_generate",
        lambda *args, **kwargs: next(respuestas),
    )

    response = client.post("/chat/", json={"message": "Haz algo"})

    assert response.status_code == 200
    assert response.json() == {
        "response": "No encontré esa operación.",
        "function_called": "funcion_inexistente",
    }


def test_chat_convierte_typeerror_de_herramienta_en_error_controlado(
    client: TestClient,
    monkeypatch,
):
    llamada = SimpleNamespace(name="listar_gastos", args={"argumento": "incorrecto"})
    primera_respuesta = crear_respuesta(None, llamada)
    segunda_respuesta = crear_respuesta("No pude procesar los argumentos.")
    contenido_segunda_llamada = {}

    def generar(contents, config):
        if "contenido" not in contenido_segunda_llamada:
            contenido_segunda_llamada["contenido"] = None
            return primera_respuesta, "modelo-test"

        contenido_segunda_llamada["contenido"] = contents
        return segunda_respuesta, "modelo-test"

    def herramienta_con_error(**kwargs):
        raise TypeError("argumento no válido")

    monkeypatch.setattr(chat, "_generate", generar)
    monkeypatch.setitem(
        chat.FUNCTION_IMPLEMENTATIONS,
        "listar_gastos",
        herramienta_con_error,
    )

    response = client.post("/chat/", json={"message": "Lista mis gastos"})

    assert response.status_code == 200
    assert response.json()["function_called"] == "listar_gastos"

    ultimo_contenido = contenido_segunda_llamada["contenido"][-1]
    function_response = ultimo_contenido.parts[0].function_response
    assert function_response.response == {
        "result": {"error": "Argumentos inválidos para la función."}
    }


def test_chat_devuelve_mensaje_si_falla_segunda_llamada(
    client: TestClient,
    monkeypatch,
):
    class ErrorApiFalso(Exception):
        pass

    monkeypatch.setattr(chat, "APIError", ErrorApiFalso)

    llamada = SimpleNamespace(name="funcion_inexistente", args={})
    primera_respuesta = crear_respuesta(None, llamada)
    cantidad_llamadas = 0

    def generar(*args, **kwargs):
        nonlocal cantidad_llamadas
        cantidad_llamadas += 1

        if cantidad_llamadas == 1:
            return primera_respuesta, "modelo-test"

        raise ErrorApiFalso("falló la segunda llamada")

    monkeypatch.setattr(chat, "_generate", generar)

    response = client.post("/chat/", json={"message": "Haz algo"})

    assert response.status_code == 200
    assert response.json() == {
        "response": (
            "He consultado los datos pero no he podido redactar la respuesta. "
            "Inténtalo de nuevo."
        ),
        "function_called": "funcion_inexistente",
    }
