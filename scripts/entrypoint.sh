#!/usr/bin/env bash

export GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}
export AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT=${AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT}
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

airflow db upgrade

airflow db init

airflow users create -r Admin -u admin -p admin -e admin@example.com -f admin -l airflow
# "$_AIRFLOW_WWW_USER_USERNAME" -p "$_AIRFLOW_WWW_USER_PASSWORD"

airflow webserver