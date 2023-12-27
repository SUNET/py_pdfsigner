from py_pdfsigner.context import ContextRequest
from py_pdfsigner.models import StatusReply

async def update_status(req: ContextRequest)-> None:
    req.app.status = StatusReply(
        status="OK",
    )