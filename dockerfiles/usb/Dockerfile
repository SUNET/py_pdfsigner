FROM debian:stable

RUN addgroup --system sunet && adduser --system --shell /bin/false --ingroup sunet sunet

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    netcat-traditional \
    dnsutils \
    git \
    openssl \
    vim-tiny \
    bsdmainutils \
    curl \
    wget \
    unzip \ 
    python3-venv \
    iputils-ping \
    procps \
    net-tools \
    bind9-host \
    procps \
    opensc \
    usbutils \
    libpcsclite1 \
    libgdk-pixbuf2.0-0 \
    libgtk2.0-0 \
    libpango-1.0-0

RUN rm -rf /var/lib/apt/lists/*

WORKDIR /opt/sunet
COPY requirements.txt ./
RUN python3 -mvenv /opt/sunet/venv
RUN /opt/sunet/venv/bin/pip install --upgrade pip wheel
RUN /opt/sunet/venv/bin/pip install --index-url https://pypi.sunet.se/simple -r /opt/sunet/requirements.txt


RUN cd /tmp/ && wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb
RUN dpkg -i /tmp/libssl1.1_1.1.0g-2ubuntu4_amd64.deb

RUN cd /tmp/ && wget https://www.globalsign.com/en/safenet-drivers/USB/10.7/Safenet_Linux_Installer_DEB_x64.zip
RUN unzip /tmp/Safenet_Linux_Installer_DEB_x64.zip -d /tmp/
RUN dpkg -i /tmp/safenetauthenticationclient_10.7.77_amd64.deb

RUN mkdir -p /var/log/sunet && chown sunet: /var/log/sunet && chmod 770 /var/log/sunet


COPY src ./src
COPY dockerfiles/start.sh ./

EXPOSE 8080

HEALTHCHECK --interval=27s CMD curl --max-time 20 http://localhost:8080/status/ | grep -q OK

ENTRYPOINT [ "/bin/bash"]

CMD [ "/opt/sunet/start.sh" ]