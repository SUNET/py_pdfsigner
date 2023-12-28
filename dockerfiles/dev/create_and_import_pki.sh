#!/usr/bin/env bash

set -e 

out_folder="opt/sunet/hsm"
if [[ ! -d  ${out_folder} ]]; then
    mkdir -p ${out_folder}
fi

pkcs11_pin="1234"
pkcs11_module="/usr/lib/softhsm/libsofthsm2.so"
pkcs11_label="test_label"
pkcs11_key_label="test_key_label"
pkcs11_cert_label="test_cert_label"

ls -lah "${pkcs11_module}"

id

ls -lah /var/lib/softhsm/tokens/
cat /etc/softhsm/softhsm2.conf
cat /etc/group


clean_hsm() {
    printf "clean hsm\n"
    softhsm2-util --delete-token --token "${pkcs11_label}"
    rm  -r /var/lib/softhsm/tokens/*
    printf "done!\n"
}

init_hsm() {
    printf "Init hsm\n"
    pkcs11-tool --module "${pkcs11_module}" --init-token --init-pin --login --pin "${pkcs11_pin}" --so-pin "${pkcs11_pin}" --label "${pkcs11_label}"
    printf "done!\n"
}

create_pki() {
    printf "create PKI\n"
    openssl req -x509 -newkey rsa:4096 -keyout "${out_folder}"/private.pem -out "${out_folder}"/cert.pem -sha256 -days 3650 -nodes -subj "/C=SE/ST=Stockholm/L=Stockholm/O=SUNET/OU=Infrastructure/CN=example.com"
    printf "done!\n"
}

convert_pem2der() {
    printf "convert pem to der\n"
    openssl rsa -in "${out_folder}"/private.pem -outform DER -out "${out_folder}"/private.der
    openssl x509 -in "${out_folder}"/cert.pem -outform DER -out "${out_folder}"/cert.der
    printf "done!\n"
}

import_private_key() {
    printf "import private key\n"
    pkcs11-tool --module "${pkcs11_module}" -l --pin "${pkcs11_pin}" --write-object "${out_folder}"/private.der --type privkey --id 1001 --label "${pkcs11_key_label}"
    printf "done!\n"
}

import_cert() {
    printf "import certificate\n"
    pkcs11-tool --module "${pkcs11_module}" -l --pin "${pkcs11_pin}" --write-object "${out_folder}"/cert.der --type cert --id 2002 --label "${pkcs11_cert_label}"
    printf "done!\n"
}

pkcs11_list() {
    printf "print pkcs11 objects\n"
    pkcs11-tool --module "${pkcs11_module}" -L --pin "${pkcs11_pin}" -T -O -I
    printf "done!\n"
}

create_run_once() {
    touch "${out_folder}"/.run_once
    date > "${out_folder}"/.run_once
}

prevent_run_more_than_once() {
    if [[ -f  "${out_folder}"/.run_once ]]; then
        printf "this script can only run once!\n"
        exit 0
    fi
}

show_slots() {
    softhsm2-util --show-slots
}

#prevent_run_more_than_once
#clean_hsm
init_hsm
create_pki

convert_pem2der
import_private_key
import_cert

pkcs11_list
show_slots

create_run_once