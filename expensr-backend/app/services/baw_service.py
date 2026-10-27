import json
import os
from typing import Any

import httpx


def start_baw_instance(gasto: dict[str, Any]) -> str | None:
    """Inicia ExpenseValidation en BAW y devuelve el ID de instancia."""
    base_url = os.getenv("BAW_BASE_URL", "").rstrip("/")
    user = os.getenv("BAW_USER", os.getenv("BAW_USERNAME", "")).strip()
    password = os.getenv("BAW_PASSWORD", "")
    bpd_id = os.getenv("BAW_BPD_ID", "").strip()
    process_app_id = os.getenv("BAW_PROCESS_APP_ID", "").strip()

    missing = [
        name
        for name, value in (
            ("BAW_BASE_URL", base_url),
            ("BAW_USER", user),
            ("BAW_PASSWORD", password),
            ("BAW_BPD_ID", bpd_id),
            ("BAW_PROCESS_APP_ID", process_app_id),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Falta configuración BAW: {', '.join(missing)}")

    ca_bundle = os.getenv("BAW_CA_BUNDLE", "").strip()
    verify: str | bool = ca_bundle if ca_bundle else True

    with httpx.Client(
        base_url=base_url,
        auth=(user, password),
        verify=verify,
        timeout=30.0,
    ) as client:
        login_response = client.post(
            "/bpm/system/login",
            json={"refresh-groups": False, "requested-lifetime": 7200},
            headers={"Accept": "application/json"},
        )
        login_response.raise_for_status()

        csrf_token = login_response.json().get("csrf_token")
        if not csrf_token:
            raise RuntimeError("BAW no devolvió el token CSRF.")

        params = {
            "gasto_id": gasto["id"],
            "empleado": gasto["empleado"],
            "fecha": str(gasto["fecha"]),
            "concepto": gasto["concepto"],
            "categoria": gasto["categoria"],
            "importe": float(gasto["importe"]),
            "adjunto_url": gasto.get("adjunto_url") or "",
        }

        query = {
            "action": "start",
            "bpdId": bpd_id,
            "processAppId": process_app_id,
            "params": json.dumps(params, ensure_ascii=False),
        }

        response = client.post(
            "/rest/bpm/wle/v1/process",
            params=query,
            headers={
                "Accept": "application/json",
                "BPMCSRFToken": csrf_token,
            },
        )

        if response.is_error:
            raise RuntimeError(
                f"BAW HTTP {response.status_code}: {response.text[:2000]}"
            )

        result = response.json()
        result_data = result.get("data") or result.get("Data") or {}

        if result.get("status") == "error" or result_data.get("status") == "error":
            raise RuntimeError(f"BAW devolvió un error: {response.text[:2000]}")

        instance_id = (
            result_data.get("piid")
            or result_data.get("processInstanceId")
        )
        if not instance_id:
            raise RuntimeError(
                f"BAW no devolvió el ID de instancia: {response.text[:2000]}"
            )

        return str(instance_id)
