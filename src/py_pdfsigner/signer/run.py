from py_pdfsigner.signer.queue import SigningQueue
from retask import Task

if __name__ == "__main__":
    sq = SigningQueue()

    while True:
        sign_task = sq.sign_queue.wait()
        sign_data = sq.unmarshal(sign_task.data)
        sq.logger.info("Received signing task urn: %s transaction_id: %s", sign_task.urn, sign_data.transaction_id)
        signedPDF = sq.sign(in_data=sign_data)
        sq.logger.info("signedpdf: %s", signedPDF)

        s =  signedPDF.model_dump()
        add_signed_task = Task(data=signedPDF.model_dump())
        
        sq.add_signed_queue.enqueue(task=add_signed_task)