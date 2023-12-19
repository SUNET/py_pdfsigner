from py_pdfsigner.models import PDFSignReply, PDFSignRequest, PDFValidateReply, PDFValidateRequest

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

async def sign(req: ContextRequest, transaction_id: str, base64_pdf: str, reason: str, location: str)-> PDFSignReply:
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