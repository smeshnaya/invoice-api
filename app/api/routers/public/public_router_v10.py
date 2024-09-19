import logging

from fastapi import APIRouter, status, Response

from app.api.paths import Paths
from app.config.constants import API_BASE_URL

API_V10 = "v1.0"

public_router_v10 = APIRouter(
    prefix=f"{API_BASE_URL}/{API_V10}",
    tags=[f"public/{API_V10}"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
    },
)

logger = logging.getLogger(__name__)


@public_router_v10.get(Paths.status.value)
async def get_available_experiments():
    return Response(status_code=200)
