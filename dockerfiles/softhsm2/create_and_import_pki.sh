#!/usr/bin/env bash

set -e 

out_folder="developer_pki/hsm"
if [[ ! -d  ${out_folder} ]]; then
    mkdir -p ${out_folder}
fi

softhsm2-util --init-token --slot 0 --label "developer-label" --pin 1234 --so-pin 1234

openssl req -x509 -newkey rsa:4096 -keyout "${out_folder}"/private.pem -out "${out_folder}"/cert.pem -sha256 -days 3650 -nodes -subj "/C=SE/ST=Stockholm/L=Stockholm/O=SUNET/OU=Infrastructure/CN=example.com"

softhsm2-util --pin 1234 --import "${out_folder}"/private.pem --label developer-label --token developer-label --id A1B2