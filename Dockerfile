FROM apache/airflow:2.3.2

ENV AIRFLOW_HOME=/Users/eugene/Personal_Projects/Data_Project/app/airflow

USER root

RUN apt-get update -qq && apt-get install vim -qqq

COPY requirements.txt .

USER $AIRFLOW_UID

RUN pip install -r requirements.txt --use-deprecated=legacy-resolver

SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]

USER root

ARG CLOUD_SDK_VERSION=322.0.0

ENV GCLOUD_HOME=/Users/eugene/google-cloud-sdk

ENV PATH="${GCLOUD_HOME}/bin/:${PATH}"

RUN DOWNLOAD_URL="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz" \
    && TMP_DIR="$(mktemp -d)" \
    && curl -fL "${DOWNLOAD_URL}" --output "${TMP_DIR}/google-cloud-sdk.tar.gz" \
    && mkdir -p "${GCLOUD_HOME}" \
    && tar xzf "${TMP_DIR}/google-cloud-sdk.tar.gz" -C "${GCLOUD_HOME}" --strip-components=1 \
    && "${GCLOUD_HOME}/install.sh" \
       --bash-completion=false \
       --path-update=false \
       --usage-reporting=false \
       --quiet \
    && rm -rf "${TMP_DIR}" \
    && gcloud --version

WORKDIR $AIRFLOW_HOME

COPY scripts scripts

RUN chmod +x scripts

USER $AIRFLOW_UID