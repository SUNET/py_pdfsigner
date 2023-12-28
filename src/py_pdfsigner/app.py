import logging
import time

from fastapi import FastAPI
from pyhanko.sign.pkcs11 import open_pkcs11_session

from py_pdfsigner.context import ContextRequestRoute
from py_pdfsigner.exceptions import RequestValidationError, validation_exception_handler, HTTPErrorDetail, http_error_detail_handler, unexpected_error_handler
from py_pdfsigner.routes.document import pdf_router
from py_pdfsigner.routes.status import status_router
from py_pdfsigner.config import parse, CFG
from py_pdfsigner.models import StatusReply
from pkcs11 import Session, UserAlreadyLoggedIn

class PDFSIGNERAPP(FastAPI):
    # Create fastapi app
    def __init__(self, service_name: str = "py_pdfsigner"):
        self.service_name = service_name
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.DEBUG)
        self.status: StatusReply = StatusReply(
            status="OK",
            last_check=int(time.time()),
            next_check=int(time.time()) + 60,
        )

        super().__init__()

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        ch.setFormatter(formatter)

        self.logger.addHandler(ch)

        self.config: CFG = parse(log=self.logger)

        self.pkcs11_try = 0

        self.session: Session
        self.init_pkcs11_session()

    def init_pkcs11_session(self) -> None:
        self.logger.info("init pkcs11 session")
        try:
            self.session = open_pkcs11_session(
                lib_location=self.config.pkcs11_module, 
                slot_no=self.config.pkcs11_slot, 
                token_label=self.config.pkcs11_label,
                user_pin=self.config.pkcs11_pin,
            )
        except UserAlreadyLoggedIn:
            self.logger.info("pkcs11 user already logged in!")

def init_app(service_name: str = "py_pdfsigner") -> PDFSIGNERAPP:
    """init pdf signing app"""
    app = PDFSIGNERAPP(service_name=service_name)
    app.router.route_class = ContextRequestRoute

    # Routers
    app.include_router(pdf_router)
    app.include_router(status_router)

    # Exception handling
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPErrorDetail, http_error_detail_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)

    app.logger.info(msg="app running...")
    return app