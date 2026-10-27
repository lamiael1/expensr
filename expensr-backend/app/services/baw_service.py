import json
import os
from typing import Any  # <--- Añadir esta importación

import httpx


def start_baw_instance(
    gasto: dict[str, Any],
) -> str | None:  # <--- Cambiar 'dict' por 'dict[str, Any]'
    """Inicia el proceso ExpenseValidation en IBM BAW y devuelve su piid."""
    base_url = os.getenv("BAW_BASE_URL", "").rstrip("/")
    user = os.getenv("BAW_USER", os.getenv("BAW_USERNAME", ""))
    password = os.getenv("BAW_PASSWORD", "")
    bpd_id = os.getenv("BAW_BPD_ID", "")
    branch_id = os.getenv("BAW_BRANCH_ID", "")

    if not (base_url and user and password and bpd_id):
        return None

    ca_bundle = os.getenv("BAW_CA_BUNDLE", "").strip()
    verify = ca_bundle if ca_bundle else True

    with httpx.Client(
        base_url=base_url,
        auth=(user, password),
        verify=verify,
        timeout=20.0,
    ) as client:
        # 1. Login y obtención de token CSRF
        login_res = client.post(
            "/bpm/system/login",
            json={"refresh-groups": False, "requested-lifetime": 7200},
            headers={"Accept": "application/json"},
        )
        login_res.raise_for_status()
        csrf_token = login_res.json().get("csrf_token")

        if not csrf_token:
            return None

        # 2. Iniciar instancia del proceso
        process_payload = {
            "action": "start",
            "bpdId": bpd_id,
            "params": json.dumps({"gasto": gasto}),
        }
        if branch_id:
            process_payload["branchId"] = branch_id

        res = client.post(
            "/rest/bpm/wle/v1/process",
            data=process_payload,
            headers={"Accept": "application/json", "BPMCSRFToken": csrf_token},
        )
        res.raise_for_status()

        data = res.json().get("data", {})
        instance_id = data.get("piid") or data.get("processInstanceId")
        return str(instance_id) if instance_id else None
