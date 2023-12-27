import time
from typing import Any

from fastapi import APIRouter

from py_pdfsigner.exceptions import ErrorDetail
from py_pdfsigner.models import StatusReply
from py_pdfsigner.context import ContextRequestRoute, ContextRequest


status_router = APIRouter(
    route_class=ContextRequestRoute,
    prefix="/status",
    responses={
        400: {"description": "Bad request", "model": ErrorDetail},
        404: {"description": "Not found", "model": ErrorDetail},
        500: {"description": "Internal server error", "model": ErrorDetail},
    },
)

@status_router.get("/", response_model=StatusReply)
async def get_status(req: ContextRequest) ->Any:
    """/status/, GET method."""

    return req.app.status
