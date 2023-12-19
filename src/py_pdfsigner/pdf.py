from pyhanko.pdf_utils.reader import PdfFileReader
from typing import Optional

def get_transaction_id_from_keywords(pdf: PdfFileReader) -> Optional[str]:
    """simple function to get transaction_id from a list of keywords"""
    for keyword in pdf.document_meta_view.keywords:
        entry = keyword.split(sep=":")
        if entry[0] == "transaction_id":
            #req.app.logger.info(msg=f"found transaction_id: {entry[1]}")
            return entry[1]
    return None