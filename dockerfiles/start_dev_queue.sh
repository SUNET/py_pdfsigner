#!/usr/bin/env bash

#service_instance="api"
if [[ $# -eq 0 ]] || [[ $1 == "api" ]] ; then
    service_instance="api"
elif [[ $1 == "queue" ]]; then
     service_instance="queue"
else
     echo "Unknown service instance: ${1}"
     exit 1
fi

printf "Starting service instance: %s\n" "${service_instance}"


set -e

. /opt/sunet/create_and_import_pki.sh

. /opt/sunet/venv/bin/activate



app_entrypoint="py_pdfsigner.queue"
app_name="py_pdfsigner"
base_dir="/opt/sunet"
project_dir="${base_dir}/src"
log_dir="/var/log/sunet"
state_dir="${base_dir}/run"
workers="1"
worker_class="sync"
worker_threads="1"
worker_timeout="30"

# set PYTHONPATH if it is not already set using Docker environment
export PYTHONPATH=${PYTHONPATH-${project_dir}}
echo "PYTHONPATH=${PYTHONPATH}"

export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}/opt/sunet/venv"

echo ""
echo "$0: Starting ${app_name}"

#exec start-stop-daemon --start -c root:root --exec \
#     /opt/sunet/venv/bin/gunicorn \
#     --pidfile "${state_dir}/${app_name}.pid" -- \
#     --bind 0.0.0.0:8080 \
#     --workers "${workers}" \
#     --worker-class "${worker_class}" \
#     --threads "${worker_threads}" \
#     --timeout "${worker_timeout}" \
#     --access-logfile "${log_dir}/${app_name}-access.log" \
#     --error-logfile "${log_dir}/${app_name}-error.log" \
#     --capture-output \
#      -k uvicorn.workers.UvicornWorker \
#     "${app_entrypoint}"

exec start-stop-daemon --start -c root:root --exec \
     /opt/sunet/venv/bin/python \
     --pidfile py_pdfsigner.pid --\
     -m ${app_entrypoint}