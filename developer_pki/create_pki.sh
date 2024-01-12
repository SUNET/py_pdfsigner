#!/usr/bin/env bash

set -e 

if [ ! -f pki.ext ]; then
	cat > pki.ext <<EOF
# v3.ext
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = example.com
EOF
fi

#out_folder="/app/trusted_keys"
out_folder="./developer_pki/pki"
if [[ ! -d  ${out_folder} ]]; then
    mkdir -p ${out_folder}
fi

#Generate keyfiles with
printf "Generating keyfiles in %s\n" ${out_folder}
ret=$(openssl ecparam -name secp256r1 -genkey -noout -out "${out_folder}"/private.pem)
if [[ ${ret} -ne 0 ]]; then
    echo "Failed to generate private key"
    exit 1
fi
printf "Done\n\n"

printf "Converting keyfiles to DER format\n"
ret=$(openssl ec -in "${out_folder}"/private.pem -outform DER -out "${out_folder}"/private.der)
if [[ ${ret} -ne 0 ]]; then
    echo "Failed to convert private key to DER format"
    exit 1
fi
printf "Done\n\n"

printf "Generating public key\n"
ret=$(openssl ec -in ${out_folder}/private.pem -pubout -out ${out_folder}/public.pem)
if [[ ${ret} -ne 0 ]]; then
    echo "Failed to generate public key"
    exit 1
fi
printf "Done\n\n"

printf "Converting public key to DER format\n"
ret=$(openssl ec -in ${out_folder}/private.pem -pubout -outform DER -out ${out_folder}/public.der)
if [[ ${ret} -ne 0 ]]; then
    echo "Failed to convert public key to DER format"
    exit 1
fi
printf "Done\n\n"

#Generate csr
printf "Generating csr\n"
ret=$(openssl req -nodes -keyform der -key "${out_folder}"/private.der -keyout "${out_folder}"/example.key -out "${out_folder}"/example.csr -subj "/C=SE/ST=Stockholm/L=Stockholm/O=SUNET/OU=Infrastructure/CN=example.com" -new)
if [[ ${ret} -ne 0 ]]; then
    echo "Failed to generate csr"
    exit 1
fi
printf "Done\n\n"

#Create (selfsigned) certificate
printf "Generating certificate\n"
ret=$(openssl x509 -signkey "${out_folder}"/private.pem -in ${out_folder}/example.csr -req -days 3650 -out ${out_folder}/example.crt -extfile pki.ext)
if [[ "${ret}" -ne 0 ]]; then
    echo "Failed to generate certificate"
    exit 1
fi
printf "Done\n\n"

rm pki.ext

