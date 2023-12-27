import time
from typing import Any

from fastapi import APIRouter

from py_pdfsigner.exceptions import ErrorDetail
from py_pdfsigner.models import PDFSignReply, PDFSignRequest, PDFValidateReply, PDFValidateRequest
from py_pdfsigner.context import ContextRequestRoute, ContextRequest
from py_pdfsigner.utils.documents import sign, validate


pdf_router = APIRouter(
    route_class=ContextRequestRoute,
    prefix="/document",
    responses={
        400: {"description": "Bad request", "model": ErrorDetail},
        404: {"description": "Not found", "model": ErrorDetail},
        500: {"description": "Internal server error", "model": ErrorDetail},
    },
)

@pdf_router.post("/pdf/sign", response_model=PDFSignReply)
async def post_document_pdf_sign(req: ContextRequest, in_data: PDFSignRequest) ->Any:
    """/document/pdf/sign, POST method."""

    req.app.logger.info(f"Received a base64 PDF, transaction_id: {in_data.transaction_id}")

    reply = sign(
        req=req,
        transaction_id=in_data.transaction_id,
        base64_pdf=in_data.data,
        reason=in_data.reason,
        create_ts=int(time.time()),
        error="",
    )
    return reply


@pdf_router.post("/pdf/validate", response_model=PDFValidateReply)
async def post_document_pdf_validate(req: ContextRequest, in_data: PDFValidateRequest) -> Any:
    """/document/pdf/validate, POST method."""

    req.app.logger.info("Trying to validate a PDF")

    reply = validate(
        req=req,
        base64_pdf=in_data.data,
    )
    return reply
