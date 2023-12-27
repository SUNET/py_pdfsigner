from io import BytesIO
import base64
import time
from typing import Optional

from py_pdfsigner.models import PDFSignReply, PDFValidateReply 
from py_pdfsigner.context import ContextRequest

from pyhanko.sign.signers.pdf_signer import PdfSigner
from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.pkcs11 import PKCS11Signer
from pyhanko_certvalidator import ValidationContext
from pyhanko.keys import load_cert_from_pemder
from pyhanko.pdf_utils.crypt.api import PdfKeyNotAvailableError
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import async_validate_pdf_signature

async def sign(req: ContextRequest, transaction_id: str, base64_pdf: str, reason: str, location: str, name: str, contact_info: str)-> PDFSignReply:
    pdf_writer = IncrementalPdfFileWriter(input_stream=BytesIO(base64.urlsafe_b64decode(base64_pdf)), strict=False)
    pdf_writer.document_meta.keywords = [f"transaction_id:{transaction_id}"]

    #print(f"pin: {req.app.pin}, label: {req.app.label}, module: {req.app.module}, cert_label: {req.app.cert_label}, key_label: {req.app.key_label}")

    pkcs11_signer = PKCS11Signer(
        pkcs11_session=req.app.session,
        cert_label=req.app.config.pkcs11_cert_label,
        key_label=req.app.config.pkcs11_key_label,
        use_raw_mechanism=True,
    )

    signature_meta = signers.PdfSignatureMetadata(
        field_name="Signature1",
        location=location,
        reason=reason,
        name=name,
        contact_info=contact_info,
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
        err_msg = f"py_pdfsigner: input pdf is encrypted, err: {_e}"
        print("error: " + err_msg)

        return PDFSignReply(
            transaction_id=transaction_id,
            data=None,
            create_ts=int(time.time()),
            error=err_msg,
        )

    base64_encoded = base64.b64encode(signed_pdf.getvalue()).decode("utf-8")

    signed_pdf.close()
    
    return PDFSignReply(
        transaction_id=transaction_id,
        data=base64_encoded,
        create_ts=int(time.time()),
        error="",
    )

async def validate(req: ContextRequest, base64_pdf: str) -> PDFValidateReply:
    pdf = PdfFileReader(BytesIO(base64.b64decode(base64_pdf.encode("utf-8"), validate=True)), strict=False)

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

def get_transaction_id_from_keywords(req: ContextRequest, pdf: PdfFileReader) -> Optional[str]:
    """simple function to get transaction_id from a list of keywords"""
    for keyword in pdf.document_meta_view.keywords:
        entry = keyword.split(sep=":")
        if entry[0] == "transaction_id":
            req.app.logger.info(msg=f"found transaction_id: {entry[1]}")
            return entry[1]
    return None