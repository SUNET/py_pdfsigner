from pydantic import BaseModel
from typing import Optional
import yaml
import os
import sys
from logging import Logger


class CFG(BaseModel):
    pkcs11_label: str
    pkcs11_pin: str
    pkcs11_module: str
    pkcs11_key_label: Optional[str] = None
    pkcs11_cert_label: Optional[str] = None
    pkcs11_slot: int

def parse(log: Logger) -> CFG:
    file_name = os.getenv("CONFIG_YAML")
    if file_name is None:
        log.error("no config file env variable found")
        sys.exit(1)

    try:
        with open(file_name, "r")as f:
             data = yaml.load(f, yaml.FullLoader)
             cfg = CFG.model_validate(data["py_pdfsigner"])
    except Exception as e:
            log.error(f"open file {file_name} failed, error: {e}")
            sys.exit(1)
    return cfg