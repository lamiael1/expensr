from tests.factories import crear_gasto


def test_update_baw_validation(client, db_session):

    gasto = crear_gasto(db_session)

    response = client.patch(
        f"/baw/expenses/{gasto.id}/validation",
        json={
            "centro_coste": "CC-COMERCIAL-01",
            "requiere_revision_manager": True,
            "estado": "PENDIENTE_BAW",
        },
    )

    assert response.status_code == 200

    db_session.refresh(gasto)

    assert gasto.centro_coste == "CC-COMERCIAL-01"

    assert gasto.requiere_revision_manager is True

    assert gasto.fecha_validacion_baw is not None


def test_update_baw_validation_gasto_inexistente(client):

    response = client.patch(
        "/baw/expenses/9999/validation",
        json={
            "centro_coste": "CC-COMERCIAL-01",
            "requiere_revision_manager": False,
            "estado": "PENDIENTE_BAW",
        },
    )

    assert response.status_code == 404


def test_update_baw_decision(client, db_session):

    gasto = crear_gasto(db_session)

    response = client.patch(
        f"/baw/expenses/{gasto.id}/decision",
        json={"estado": "APROBADO_BAW", "comentario_baw": "OK, aprobado."},
    )

    assert response.status_code == 200

    db_session.refresh(gasto)

    assert gasto.estado == "APROBADO_BAW"

    assert gasto.comentario_baw == "OK, aprobado."


def test_update_baw_decision_gasto_inexistente(client):

    response = client.patch(
        "/baw/expenses/9999/decision",
        json={"estado": "RECHAZADO_BAW", "comentario_baw": "No procede."},
    )

    assert response.status_code == 404
