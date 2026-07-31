"""Weekly full-corpus reindex -- rebuilds embeddings for every document, useful
after an embedding model upgrade. Also Docker/Stage-4-oriented, same as above."""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {"owner": "finrag", "retries": 1, "retry_delay": timedelta(minutes=10)}


def reindex_all_documents(**context):
    import requests
    import os
    source_dir = "/data/raw"
    api_url = "http://finrag-api:8000/ingest"
    for fname in os.listdir(source_dir):
        with open(f"{source_dir}/{fname}", "rb") as f:
            requests.post(api_url, files={"file": f})


with DAG(
    dag_id="weekly_reindex_dag",
    default_args=default_args,
    schedule_interval="@weekly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    PythonOperator(task_id="reindex_all_documents", python_callable=reindex_all_documents)
