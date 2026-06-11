import logging

import httpx

from config import settings
from shared.schemas.optimization import SolveRequest as LinearSolveRequest
from shared.schemas.topsis import SolveRequest as TSSolveRequest
from shared.schemas.electre import SolveRequest as ESolveRequest

logger = logging.getLogger(__name__)

_transport = httpx.HTTPTransport(retries=3)
_client = httpx.Client(transport=_transport, timeout=10)


def solve_via_api(req: LinearSolveRequest | TSSolveRequest | ESolveRequest) -> dict:
    if isinstance(req, ESolveRequest):
        endpoint = f"{settings.API_BASE_URL}/solvers/electre"
    elif isinstance(req, TSSolveRequest):
        endpoint = f"{settings.API_BASE_URL}/solvers/topsis"
    else:
        endpoint = f"{settings.API_BASE_URL}/solvers/linear"

    try:
        response = _client.post(
            endpoint,
            json=req.model_dump(mode="json"),
        )
        response.raise_for_status()
    except httpx.ConnectError:
        logger.error("Не може да се свърже със сървъра на адрес %s", settings.API_BASE_URL)
        raise ValueError("Сървърът не е достъпен. Проверете дали е стартиран.")
    except httpx.TimeoutException:
        logger.error("Времето за отговор от сървъра изтече: %s", endpoint)
        raise ValueError("Времето за отговор от сървъра изтече. Опитайте отново.")
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail")
        except Exception:
            detail = exc.response.text
        logger.warning("Сървърът върна грешка %s: %s", exc.response.status_code, detail)
        raise ValueError(detail)

    return response.json()
