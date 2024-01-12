from py_pdfsigner.validator.queue import ValidatorQueue
from retask import Task

#"""Run the PDF service."""
#from py_pdfsigner.validator.api import init_api
#
#api = init_api()

if __name__ == "__main__":
    vq = ValidatorQueue()

    while True:
        validate_task = vq.validate_queue.wait()
        vq.logger.info("Received validate task urn: %s", validate_task.urn)
        if isinstance(validate_task, bool):
            vq.logger.error("No task received, timeout!")
            exit(0)

        validate_data = vq.unmarshal(validate_task.data)

        validated_pdf = vq.validate(in_data=validate_data)

        vq.validate_queue.send(task=validate_task, result=validated_pdf.model_dump())