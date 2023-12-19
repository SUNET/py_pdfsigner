from .main import PDFAPI, pdf_router
from .context import ContextRequestRoute
from .exceptions import RequestValidationError, validation_exception_handler, HTTPErrorDetail, http_error_detail_handler, unexpected_error_handler

def init_api(service_name: str = "pdf_api") -> PDFAPI:
    """init PDF_API"""
    app = PDFAPI(service_name=service_name)
    app.router.route_class = ContextRequestRoute

    # Routers
    app.include_router(pdf_router)
    #app.include_router(status_router)

    # Exception handling
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPErrorDetail, http_error_detail_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)

    app.logger.info(msg="app running...")
    return app

api = init_api()