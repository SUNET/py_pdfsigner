FROM debian:bookworm

EXPOSE 8080/tcp

RUN apt-get update \
    && apt-get install -y \
    python3-pip \
    python3-dev \
    libsofthsm2-dev \
    pkcs11-dump \
    python3 \
    build-essential \
    opensc \
    wget \
    swig \
    curl \
    unzip \
    libz-dev \
    dnsutils \
    mercurial \
    python3-venv \
    procps \
    opensc-pkcs11 \
    usbutils \
    libpcsclite1 \
    libgdk-pixbuf2.0-0 \
    libgtk2.0-0 \
    libpango-1.0-0

RUN rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN python3 -m venv /app/venv

RUN /app/venv/bin/pip3 install --require-hashes -r /app/requirements.txt

RUN wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb
RUN dpkg -i ./libssl1.1_1.1.0g-2ubuntu4_amd64.deb

RUN wget https://www.globalsign.com/en/safenet-drivers/USB/10.7/Safenet_Linux_Installer_DEB_x64.zip
RUN unzip Safenet_Linux_Installer_DEB_x64.zip
RUN dpkg -i ./safenetauthenticationclient_10.7.77_amd64.deb

COPY ./src /app/src
COPY ./logging.json /app/logging.json

CMD sh -c '. /app/venv/bin/activate && uvicorn app.src.py_pdfsigner.run:api --log-config ./app/logging.json --host 0.0.0.0 --port 8080 --workers 1 --header server:pkcs11_ca'