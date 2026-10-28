import pytest

from app.db import database


class SesionFalsa:
    def __init__(self):
        self.cerrada = False

    def close(self):
        self.cerrada = True


def test_get_db_entrega_y_cierra_la_sesion(monkeypatch):
    sesion = SesionFalsa()
    monkeypatch.setattr(database, "SessionLocal", lambda: sesion)

    dependencia = database.get_db()

    assert next(dependencia) is sesion

    with pytest.raises(StopIteration):
        next(dependencia)

    assert sesion.cerrada is True


def test_get_db_cierra_la_sesion_si_ocurre_una_excepcion(monkeypatch):
    sesion = SesionFalsa()
    monkeypatch.setattr(database, "SessionLocal", lambda: sesion)

    dependencia = database.get_db()
    assert next(dependencia) is sesion

    with pytest.raises(RuntimeError, match="fallo de prueba"):
        dependencia.throw(RuntimeError("fallo de prueba"))

    assert sesion.cerrada is True
