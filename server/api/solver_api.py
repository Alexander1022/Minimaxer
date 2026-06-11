import requests
from typing import Union

from server.app.config import settings
from shared.schemas.optimization import SolveRequest as LinearSolveRequest
from shared.schemas.topsis import SolveRequest as TSSolveRequest
from shared.schemas.electre import SolveRequest as ESolveRequest


def solve_via_api(req: Union[LinearSolveRequest, TSSolveRequest, ESolveRequest]) -> dict:
    if isinstance(req, ESolveRequest):
        endpoint = f"{settings.API_BASE_URL}/electre-solve"
    elif isinstance(req, TSSolveRequest):
        endpoint = f"{settings.API_BASE_URL}/topsis-solve"
    else:
        endpoint = f"{settings.API_BASE_URL}/linear-solve"

    response = requests.post(
        endpoint,
        json=req.model_dump(mode="json"),
        timeout=10,
    )

    if response.status_code != 200:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text

        raise ValueError(detail)

    return response.json()
