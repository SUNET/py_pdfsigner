import logging
from io import BytesIO
import base64
import json
import os
from typing import Optional, Iterable
from asn1crypto import x509


from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.registry import TrustRootList
from pyhanko.keys import load_cert_from_pemder
from pyhanko.pdf_utils.reader import PdfFileReader
from retask import Queue, Task

from py_pdfsigner.models import  PDFValidateRequest, PDFValidateReply
from py_pdfsigner.validator.config import parse, CFG

class ValidatorQueue:
    def __init__(self, service_name: str = "py_pdfvalidator"):
        self.service_name = service_name
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        ch.setFormatter(formatter)

        self.logger.addHandler(ch)

        self.config: CFG = parse(log=self.logger)

        #self.validation_context = ValidationContext(
        #    trust_roots=self.build_trust_roots(),
        #)

        self.validate_queue = Queue(
            name=self.config.validate_queue_name, 
            config=self.config.redis,
        )
        self.validate_queue.connect()

    def marshal(self, data: PDFValidateRequest) -> str:
        return json.dumps(data)

    def unmarshal(self, data: dict) -> PDFValidateRequest:
        return PDFValidateRequest.model_validate(data)

    def validate(self, in_data: PDFValidateRequest) -> PDFValidateReply:
        pdf = PdfFileReader(BytesIO(base64.b64decode(in_data.base64_data.encode("utf-8"), validate=False)), strict=False)

        if len(pdf.embedded_signatures) == 0:
            return PDFValidateReply(
                error="No signature found"
            )

        vc = ValidationContext(
            trust_roots=[load_cert_from_pemder("/opt/sunet/pki/example.crt")]
        )

        status = validate_pdf_signature(
            embedded_sig=pdf.embedded_signatures[0],
            signer_validation_context=vc,
        )

        transaction_id = self.get_transaction_id_from_keywords(pdf=pdf)
        self.logger.info(f"Validate a signed base64 PDF, transaction_id:{transaction_id}")

        return PDFValidateReply(
            valid_signature=status.bottom_line,
            transaction_id=transaction_id,
        )

    def get_transaction_id_from_keywords(self,pdf: PdfFileReader) -> Optional[str]:
        """simple function to get transaction_id from a list of keywords"""
        for keyword in pdf.document_meta_view.keywords:
            entry = keyword.split(sep=":")
            if entry[0] == "transaction_id":
                self.logger.info(msg=f"found transaction_id: {entry[1]}")
                return entry[1]
        return None

    def build_trust_roots(self) -> TrustRootList:
        trust_root_list = list()
        for file in os.listdir(self.config.trust_root_folder):
            filename = os.fsdecode(file)
            if filename.endswith(".crt"):
                self.logger.info(f"found trust root file: {filename}")
                trust_root_list.append(load_cert_from_pemder(self.config.trust_root_folder + "/" + filename))
        return TrustRootList(trust_root_list)