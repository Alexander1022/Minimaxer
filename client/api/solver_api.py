import requests

from config import API_BASE_URL
from shared.schemas.optimization import SolveRequest


def solve_via_api(req: SolveRequest) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/solve",
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