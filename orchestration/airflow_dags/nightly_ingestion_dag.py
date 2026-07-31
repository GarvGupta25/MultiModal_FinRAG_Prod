"""Nightly ingestion DAG -- checks a configured source folder for new documents,
ingests + embeds them, versions the data with DVC, and notifies on completion.

NOTE: designed for the Stage 4 Docker deployment (docker-compose runs a real
Airflow scheduler + webserver). Not intended to run standalone in the Colab
notebook environment.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "finrag",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def check_for_new_documents(**context):
    import os
    source_dir = os.environ.get("FINRAG_SOURCE_DIR", "/data/incoming")
    seen_path = "/data/.ingested_files.txt"
    seen = set(open(seen_path).read().split()) if os.path.exists(seen_path) else set()
    all_files = set(os.listdir(source_dir)) if os.path.isdir(source_dir) else set()
    new_files = list(all_files - seen)
    context["ti"].xcom_push(key="new_files", value=new_files)
    return new_files


def download_documents(**context):
    # Placeholder: for local/mounted source_dir this is a no-op; extend for
    # S3/GDrive/IMAP sources as needed.
    pass


def run_ingestion_pipeline(**context):
    import requests
    new_files = context["ti"].xcom_pull(key="new_files", task_ids="check_for_new_documents")
    source_dir = "/data/incoming"
    api_url = "http://finrag-api:8000/ingest"
    for fname in new_files:
        with open(f"{source_dir}/{fname}", "rb") as f:
            requests.post(api_url, files={"file": f})


def mark_ingested(**context):
    import os
    new_files = context["ti"].xcom_pull(key="new_files", task_ids="check_for_new_documents")
    seen_path = "/data/.ingested_files.txt"
    with open(seen_path, "a") as f:
        for fname in new_files:
            f.write(fname + "\n")


def dvc_commit(**context):
    import subprocess
    subprocess.run(["dvc", "add", "data/raw"], check=False)
    subprocess.run(["dvc", "push"], check=False)
    subprocess.run(["git", "add", "data/raw.dvc"], check=False)
    subprocess.run(["git", "commit", "-m", f"Data version {datetime.now().isoformat()}"], check=False)


def notify_completion(**context):
    new_files = context["ti"].xcom_pull(key="new_files", task_ids="check_for_new_documents")
    print(f"Nightly ingestion complete: {len(new_files)} new documents processed.")


with DAG(
    dag_id="nightly_ingestion_dag",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    t1 = PythonOperator(task_id="check_for_new_documents", python_callable=check_for_new_documents)
    t2 = PythonOperator(task_id="download_documents", python_callable=download_documents)
    t3 = PythonOperator(task_id="run_ingestion_pipeline", python_callable=run_ingestion_pipeline)
    t4 = PythonOperator(task_id="mark_ingested", python_callable=mark_ingested)
    t5 = PythonOperator(task_id="dvc_commit", python_callable=dvc_commit)
    t6 = PythonOperator(task_id="notify_completion", python_callable=notify_completion)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6
