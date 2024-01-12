.PHONY: docker-build-pdfsigner docker-push ci vscode_venv vscode_pip vscode_packages vscode

TOPDIR:=		$(abspath .)
SRCDIR=			$(TOPDIR)/src
SOURCE=			$(SRCDIR)/pkcs11_ca
TEST_SOURCE= 	$(TOPDIR)/tests
PYTHON=$(shell which python)
PIPCOMPILE=pip-compile -v --upgrade --generate-hashes --allow-unsafe --index-url https://pypi.sunet.se/simple
PIPSYNC=pip-sync --index-url https://pypi.sunet.se/simple --python-executable $(PYTHON)

sync_deps:
	$(PIPSYNC) requirements.txt

update_deps:
	$(PIPCOMPILE) requirements.in

test:
	PYTHONPATH=$(SRCDIR) pytest -vvv -ra --log-cli-level DEBUG

start:
	$(info Run!)
	docker-compose -f docker-compose.yaml up -d --remove-orphans

stop:
	$(info stopping)
	docker-compose -f docker-compose.yaml rm -s -f

hard_restart: stop start

start_dev:
	$(info Run dev!)
	docker-compose -f docker-compose_dev.yaml up -d --remove-orphans

stop_dev:
	$(info stopping dev)
	docker-compose -f docker-compose_dev.yaml rm -s -f

hard_dev_restart: stop_dev start_dev

ifndef VERSION
VERSION := latest                                                                                                                                                                                                                              
endif

DOCKER_PDFSIGNER 					:= docker.sunet.se/dc4eu/py_pdfsigner:$(VERSION)
DOCKER_PDFSIGNER_EXTERNAL_PKCS11 	:= docker.sunet.se/dc4eu/py_pdfsigner_external_pkcs11:$(VERSION)
DOCKER_PDFSIGNER_DEV 				:= docker.sunet.se/dc4eu/py_pdfsigner_dev:$(VERSION)
DOCKER_PDFSIGNER_USB				:= docker.sunet.se/dc4eu/py_pdfsigner_usb:$(VERSION)
DOCKER_PDFVALIDATOR_DEV 			:= docker.sunet.se/dc4eu/py_pdfvalidator_dev:$(VERSION)
DOCKER_PDFSIGNER_DEV_API 			:= docker.sunet.se/dc4eu/py_pdfsigner_dev_api:$(VERSION)

reformat:
	isort --line-width 120 --atomic --project python_x509_pkcs11 $(SOURCE)
	black --line-length 120 --target-version py39 $(SOURCE)
	isort --line-width 120 --atomic --project python_x509_pkcs11 $(TEST_SOURCE)
	black --line-length 120 --target-version py39 $(TEST_SOURCE)

static_code_analyser:
	pylint src || exit 1
	pylint tests || exit 1

typecheck:
	MYPYPATH=$(SRCDIR) mypy $(MYPY_ARGS) --namespace-packages -p python_x509_pkcs11
	MYPYPATH=$(TEST_SOURCE) mypy $(MYPY_ARGS) --namespace-packages -p python_x509_pkcs11

clean_softhsm:
	$(info Deleting and reinitialize the PKCS11 token)
	softhsm2-util --delete-token --token  $(PKCS11_TOKEN)

new_softhsm:
	$(info New SoftHSM)
	softhsm2-util --init-token --slot 0 --label $(PKCS11_TOKEN) --pin $(PKCS11_PIN) --so-pin $(PKCS11_PIN)

pkcs11-list:
	pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so -L --pin 1234 -T -O -I

docker-build-pdfsigner:
	$(info building docker image $(DOCKER_PDFSIGNER) )
	docker build --tag $(DOCKER_PDFSIGNER) --file Dockerfile .

docker-build-external_pkcs11:
	$(info building docker image $(DOCKER_PDFSIGNER_EXTERNAL_PKCS11) )
	docker build --tag $(DOCKER_PDFSIGNER_EXTERNAL_PKCS11) --file dockerfiles/external_pkcs11/Dockerfile .

docker-build-dev-api:
	$(info building docker image $(DOCKER_PDFSIGNER_DEV_API) )
	docker build --tag $(DOCKER_PDFSIGNER_DEV_API) --file dockerfiles/dev_api/Dockerfile .

docker-build-usb:
	$(info building docker image $(DOCKER_PDFSIGNER_USB) )
	docker build --tag $(DOCKER_PDFSIGNER_USB) --file dockerfiles/usb/Dockerfile .

docker-build-signer-dev:
	$(info building docker image $(DOCKER_PDFSIGNER_DEV) )
	docker build --tag $(DOCKER_PDFSIGNER_DEV) --file dockerfiles/dev/signer/Dockerfile .

docker-build-validator-dev:
	$(info building docker image $(DOCKER_PDFVALIDATOR_DEV) )
	docker build --tag $(DOCKER_PDFVALIDATOR_DEV) --file dockerfiles/dev/validator/Dockerfile .

docker-build-dev: docker-build-signer-dev docker-build-validator-dev


docker-push:
	$(info Pushing docker images)
	docker push $(DOCKER_PDFSIGNER)
	docker push $(DOCKER_PDFSIGNER_EXTERNAL_PKCS11)
	docker push $(DOCKER_PDFSIGNER_DEV_API)
	docker push $(DOCKER_PDFSIGNER_USB)
	docker push $(DOCKER_PDFSIGNER_DEV)
	docker push $(DOCKER_PDFVALIDATOR_DEV)


hard_restart: stop start
hard_restart_dev: stop_dev start_dev

docker-unit-test: docker-build-test
	$(info Run unit tests)
	docker run --rm docker.sunet.se/dc4eu/pkcs11_test:latest

ci: docker-build docker-push

developer_setup: developer_create_pki import_pki_into_hsm

developer_create_pki:
	$(info Create developer keys)
	bash -c developer_tools/create_pki.sh

import_pki_into_hsm:
	$(info Import pki into HSM)
	python3 developer_tools/import_pki_into_hsm.py


vscode_venv:
	$(info Creating virtualenv in devcontainer)
	python3 -m venv .venv

vscode_pip: vscode_venv
	$(info Installing pip packages in devcontainer)
	pip3 install --upgrade pip
	pip3 install pip-tools
	.venv/bin/pip install -r requirements.txt
# .venv/bin/mypy --install-types

vscode_packages:
	$(info Installing apt packages in devcontainer)
	sudo apt-get update
	sudo apt install -y docker.io softhsm2 opensc libsnappy-dev

# This target is used by the devcontainer.json to configure the devcontainer
vscode: vscode_packages vscode_pip sync_deps
	#. .venv/bin/activate