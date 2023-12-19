from fastapi import FastAPI, APIRouter

from py_pdfsigner.exceptions import ErrorDetail
from py_pdfsigner.models import PDFSignReply, PDFSignRequest, PDFValidateReply, PDFValidateRequest
from py_pdfsigner.context import ContextRequestRoute, ContextRequest


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