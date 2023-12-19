"""Main module, FastAPI runs from here"""
import base64
from typing import Any
import time
import os
from io import BytesIO
import logging

from fastapi import FastAPI, APIRouter

from pyhanko.sign.signers.pdf_signer import PdfSigner
from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.pkcs11 import PKCS11Signer, open_pkcs11_session
from pyhanko_certvalidator import ValidationContext
from pyhanko.keys import load_cert_from_pemder
from pyhanko.pdf_utils.crypt.api import PdfKeyNotAvailableError
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import async_validate_pdf_signature

from .pdf import get_transaction_id_from_keywords
from .context import ContextRequestRoute, ContextRequest
from .models import PDFSignReply, PDFSignRequest, PDFValidateReply, PDFValidateRequest
from .exceptions import ErrorDetail

class PDFAPI(FastAPI):
    # Create fastapi app
    def __init__(self, service_name: str = "py_pdfsigner"):
        self.service_name = service_name
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.DEBUG)

        super().__init__()

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        ch.setFormatter(formatter)

        self.logger.addHandler(ch)

        self.pin = os.getenv("PKCS11_PIN")
        self.label = os.getenv("PKCS11_LABEL")
        self.cert_label = os.getenv("PKCS11_CERT_LABEL")
        self.key_label = os.getenv("PKCS11_KEY_LABEL")
        self.module = os.getenv("PKCS11_MODULE")
        self.session = open_pkcs11_session(lib_location=self.module, slot_no=0, token_label=self.label, user_pin=self.pin)
        print("session", self.session)


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


    pdf_writer = IncrementalPdfFileWriter(input_stream=BytesIO(base64.urlsafe_b64decode(in_data.data)), strict=False)
    pdf_writer.document_meta.keywords = [f"transaction_id:{in_data.transaction_id}"]

    print(f"pin: {req.app.pin}, label: {req.app.label}, module: {req.app.module}, cert_label: {req.app.cert_label}, key_label: {req.app.key_label}")

    pkcs11_signer = PKCS11Signer(
        pkcs11_session=req.app.session,
        cert_label=req.app.cert_label,
        key_label=req.app.key_label,
        use_raw_mechanism=True,
    )

    signature_meta = signers.PdfSignatureMetadata(
        field_name="Signature1",
        location=in_data.location,
        reason=in_data.reason,
        name=in_data.name,
        contact_info=in_data.contact_info,
        subfilter=SigSeedSubFilter.ADOBE_PKCS7_DETACHED
    )

    signer = PdfSigner(
        signature_meta=signature_meta,
        signer=pkcs11_signer,
    )

    signed_pdf = BytesIO()

    try:
        await signer.async_sign_pdf(
            pdf_out=pdf_writer,
            output=signed_pdf,
        )

    except PdfKeyNotAvailableError as _e:
        err_msg = f"ca_pdfsign: input pdf is encrypted, err: {_e}"
        print("error: " + err_msg)

        return PDFSignReply(
            transaction_id=in_data.transaction_id,
            data=None,
            create_ts=int(time.time()),
            error=err_msg,
        )

    base64_encoded = base64.b64encode(signed_pdf.getvalue()).decode("utf-8")

    signed_pdf.close()

    return PDFSignReply(
        transaction_id=in_data.transaction_id,
        data=base64_encoded,
        create_ts=int(time.time()),
        error="",
    )

@pdf_router.post("/pdf/validate", response_model=PDFValidateReply)
async def post_document_pdf_validate(req: ContextRequest, in_data: PDFValidateRequest) -> Any:
    """/document/pdf/validate, POST method."""

    req.app.logger.info("Trying to validate a PDF")

    pdf = PdfFileReader(BytesIO(base64.b64decode(in_data.data.encode("utf-8"), validate=True)), strict=False)

    if len(pdf.embedded_signatures) == 0:
        return PDFValidateReply(
            error="No signature found"
        )

    validation_context = ValidationContext(
        trust_roots=[load_cert_from_pemder("/app/USERTrustRSAAddTrustCA.crt"), load_cert_from_pemder("/app/SectigoRSADocumentSigningCA.crt")],
    )

    status = await async_validate_pdf_signature(
        embedded_sig=pdf.embedded_signatures[0],
        signer_validation_context=validation_context,
    )

    transaction_id = get_transaction_id_from_keywords(pdf=pdf)
    req.app.logger.info(f"Validate a signed base64 PDF, transaction_id:{transaction_id}")

    return PDFValidateReply(
        valid_signature=status.bottom_line,
        transaction_id=transaction_id,
    )