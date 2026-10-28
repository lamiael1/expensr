import httpx
import pytest

from app.services.baw_service import start_baw_instance

CONFIG_BAW = {
    "BAW_BASE_URL": "https://baw.example.test",
    "BAW_USER": "usuario_test",
    "BAW_PASSWORD": "clave_test",
    "BAW_BPD_ID": "bpd-test",
    "BAW_PROCESS_APP_ID": "app-test",
}

GASTO = {
    "id": 25,
    "empleado": "empleado_007",
    "fecha": "2026-10-28",
    "concepto": "Comida de trabajo",
    "categoria": "Dietas",
    "importe": 50.0,
    "adjunto_url": None,
}


class RespuestaFalsa:
    def __init__(self, *, json_data=None, status_code=200, text=""):
        self._json_data = json_data or {}
        self.status_code = status_code
        self.text = text
        self.is_error = status_code >= 400

    def raise_for_status(self):
        if self.is_error:
            request = httpx.Request("POST", "https://baw.example.test")
            response = httpx.Response(
                self.status_code,
                request=request,
                text=self.text,
            )
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=request,
                response=response,
            )

    def json(self):
        return self._json_data


class ClienteFalso:
    def __init__(self, respuestas):
        self.respuestas = iter(respuestas)
        self.llamadas = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def post(self, *args, **kwargs):
        self.llamadas.append((args, kwargs))
        return next(self.respuestas)


def configurar_entorno(monkeypatch):
    for nombre, valor in CONFIG_BAW.items():
        monkeypatch.setenv(nombre, valor)

    monkeypatch.delenv("BAW_CA_BUNDLE", raising=False)


@pytest.mark.parametrize("variable", list(CONFIG_BAW))
def test_error_si_falta_configuracion_baw(monkeypatch, variable):
    configurar_entorno(monkeypatch)
    monkeypatch.delenv(variable)

    with pytest.raises(ValueError, match="Falta configuración BAW"):
        start_baw_instance(GASTO)


def test_iniciar_instancia_y_devolver_piid(monkeypatch):
    configurar_entorno(monkeypatch)
    cliente = ClienteFalso(
        [
            RespuestaFalsa(json_data={"csrf_token": "csrf-test"}),
            RespuestaFalsa(json_data={"data": {"piid": 12345}}),
        ]
    )
    monkeypatch.setattr(
        "app.services.baw_service.httpx.Client",
        lambda **kwargs: cliente,
    )

    resultado = start_baw_instance(GASTO)

    assert resultado == "12345"
    assert len(cliente.llamadas) == 2

    login_args, login_kwargs = cliente.llamadas[0]
    assert login_args == ("/bpm/system/login",)
    assert login_kwargs["json"] == {
        "refresh-groups": False,
        "requested-lifetime": 7200,
    }

    inicio_args, inicio_kwargs = cliente.llamadas[1]
    assert inicio_args == ("/rest/bpm/wle/v1/process",)
    assert inicio_kwargs["headers"]["BPMCSRFToken"] == "csrf-test"
    assert inicio_kwargs["params"]["action"] == "start"
    assert inicio_kwargs["params"]["bpdId"] == "bpd-test"
    assert inicio_kwargs["params"]["processAppId"] == "app-test"


def test_acepta_baw_username_como_alias(monkeypatch):
    monkeypatch.setenv("BAW_BASE_URL", CONFIG_BAW["BAW_BASE_URL"])
    monkeypatch.delenv("BAW_USER", raising=False)
    monkeypatch.setenv("BAW_USERNAME", "usuario_alias")
    monkeypatch.setenv("BAW_PASSWORD", CONFIG_BAW["BAW_PASSWORD"])
    monkeypatch.setenv("BAW_BPD_ID", CONFIG_BAW["BAW_BPD_ID"])
    monkeypatch.setenv("BAW_PROCESS_APP_ID", CONFIG_BAW["BAW_PROCESS_APP_ID"])
    monkeypatch.delenv("BAW_CA_BUNDLE", raising=False)

    cliente = ClienteFalso(
        [
            RespuestaFalsa(json_data={"csrf_token": "csrf-test"}),
            RespuestaFalsa(json_data={"data": {"processInstanceId": "9876"}}),
        ]
    )
    monkeypatch.setattr(
        "app.services.baw_service.httpx.Client",
        lambda **kwargs: cliente,
    )

    assert start_baw_instance(GASTO) == "9876"


def test_error_si_login_no_devuelve_token_csrf(monkeypatch):
    configurar_entorno(monkeypatch)
    cliente = ClienteFalso([RespuestaFalsa(json_data={})])
    monkeypatch.setattr(
        "app.services.baw_service.httpx.Client",
        lambda **kwargs: cliente,
    )

    with pytest.raises(RuntimeError, match="no devolvió el token CSRF"):
        start_baw_instance(GASTO)

    assert len(cliente.llamadas) == 1


def test_error_si_login_http_falla(monkeypatch):
    configurar_entorno(monkeypatch)
    cliente = ClienteFalso(
        [RespuestaFalsa(status_code=401, text="Credenciales incorrectas")]
    )
    monkeypatch.setattr(
        "app.services.baw_service.httpx.Client",
        lambda **kwargs: cliente,
    )

    with pytest.raises(httpx.HTTPStatusError):
        start_baw_instance(GASTO)


def test_error_si_inicio_http_falla(monkeypatch):
    configurar_entorno(monkeypatch)
    cliente = ClienteFalso(
        [
            RespuestaFalsa(json_data={"csrf_token": "csrf-test"}),
            RespuestaFalsa(status_code=400, text="Solicitud inválida"),
        ]
    )
    monkeypatch.setattr(
        "app.services.baw_service.httpx.Client",
        lambda **kwargs: cliente,
    )

    with pytest.raises(RuntimeError, match="BAW HTTP 400"):
        start_baw_instance(GASTO)


@pytest.mark.parametrize(
    "respuesta",
    [
        {"status": "error", "data": {"status": "error"}},
        {"Data": {"status": "error"}},
    ],
)
def test_error_si_baw_responde_con_error_en_el_cuerpo(monkeypatch, respuesta):
    configurar_entorno(monkeypatch)
    cliente = ClienteFalso(
        [
            RespuestaFalsa(json_data={"csrf_token": "csrf-test"}),
            RespuestaFalsa(json_data=respuesta, text="Error de BAW"),
        ]
    )
    monkeypatch.setattr(
        "app.services.baw_service.httpx.Client",
        lambda **kwargs: cliente,
    )

    with pytest.raises(RuntimeError, match="BAW devolvió un error"):
        start_baw_instance(GASTO)


def test_error_si_baw_no_devuelve_id_de_instancia(monkeypatch):
    configurar_entorno(monkeypatch)
    cliente = ClienteFalso(
        [
            RespuestaFalsa(json_data={"csrf_token": "csrf-test"}),
            RespuestaFalsa(json_data={"data": {}}),
        ]
    )
    monkeypatch.setattr(
        "app.services.baw_service.httpx.Client",
        lambda **kwargs: cliente,
    )

    with pytest.raises(RuntimeError, match="no devolvió el ID de instancia"):
        start_baw_instance(GASTO)
