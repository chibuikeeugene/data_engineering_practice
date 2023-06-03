# ================= impport necessary libraries ==================== #

import os
import logging

from datetime import datetime
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator
import pyarrow.csv as pv
import pyarrow.parquet as pq

AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/Users/eugene/Personal_Projects/Data_Project/app/airflow")

## ================ retrieve GCP environment variables    ===================== ##

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")


## ============== parameterization of variables for yellow taxi ====================== ##
yellow_dataset_file = "yellow_tripdata_{{execution_date.strftime(\'%Y-%m\')}}.parquet"
yellow_dataset_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{yellow_dataset_file}"
path_to_local_home = os.environ.get("AIRFLOW_HOME", "/Users/eugene/Personal_Projects/Data_Project/app/airflow")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'trips_data_all')



## ============== parameterization of variables for green taxi ====================== ##
green_dataset_file = "green_tripdata_{{execution_date.strftime(\'%Y-%m\')}}.parquet"
green_dataset_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{green_dataset_file}"


## ============== parameterization of variables for fhv ====================== ##
fhv_dataset_file = "fhv_tripdata_{{execution_date.strftime(\'%Y-%m\')}}.parquet"
fhv_dataset_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{fhv_dataset_file}"



# ================== this block of code is responsible for uploading files to google cloud storage =================== #
def upload_to_gcs(bucket, object_name, local_file):

    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}


with DAG(
    start_date=datetime(2021,1,1),
    end_date = datetime(2021,6,1),
    dag_id="data_ingestion_gcs_dag",
    schedule_interval="0 6 2 * *",
    default_args=default_args,
    catchup=True,
    max_active_runs=1,
    tags=['de'],
) as dag:
    
    download_yellow_dataset_task = BashOperator(
        task_id="download_yellow_dataset_task",
        bash_command=f"curl -sSL {yellow_dataset_url} > {path_to_local_home}/{yellow_dataset_file}"
    )

    download_green_dataset_task = BashOperator(
        task_id="download_green_dataset_task",
        bash_command=f"curl -sSL {green_dataset_url} > {path_to_local_home}/{green_dataset_file}"
    )


    download_fhv_dataset_task = BashOperator(
        task_id="download_fhv_dataset_task",
        bash_command=f"curl -sSL {fhv_dataset_url} > {path_to_local_home}/{fhv_dataset_file}"
    )


    # TODO: research and try XCOM to communicate output values between 2 tasks/operators
    local_to_gcs_task_yellow = PythonOperator(
        task_id="local_to_gcs_task_yellow",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/{yellow_dataset_file}",
            "local_file": f"{path_to_local_home}/{yellow_dataset_file}",
        },
    )


    local_to_gcs_task_green = PythonOperator(
        task_id="local_to_gcs_task_green",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw2/{green_dataset_file}",
            "local_file": f"{path_to_local_home}/{green_dataset_file}",
        },
    )



    local_to_gcs_task_fhv = PythonOperator(
        task_id="local_to_gcs_task_fhv",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw3/{fhv_dataset_file}",
            "local_file": f"{path_to_local_home}/{fhv_dataset_file}",
        },
    )





    bigquery_external_table_task_yellow = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_task_yellow",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": "yellow_table" #initially called external_table,
            },
            "externalDataConfiguration": {
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{BUCKET}/raw/{yellow_dataset_file}"],
            },
        },
    )


    bigquery_external_table_task_green = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_task_green",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": "green_table",
            },
            "externalDataConfiguration": {
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{BUCKET}/raw2/{green_dataset_file}"],
            },
        },
    )


    bigquery_external_table_task_fhv = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_task_fhv",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": "fhv_table",
            },
            "externalDataConfiguration": {
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{BUCKET}/raw3/{fhv_dataset_file}"],
            },
        },
    )



    download_yellow_dataset_task  >> local_to_gcs_task_yellow >> bigquery_external_table_task_yellow
    download_green_dataset_task  >> local_to_gcs_task_green >> bigquery_external_table_task_green
    download_fhv_dataset_task  >> local_to_gcs_task_fhv >> bigquery_external_table_task_fhv