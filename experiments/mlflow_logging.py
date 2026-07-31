"""MLflow experiment tracking for embedding-model / retrieval-config comparisons.
Uses local file-based tracking (./mlruns) -- no MLflow server needed to use this.
Call log_retrieval_experiment() after running a batch of RAGAS-scored queries
(see Stage 4 evaluation script) to compare configurations over time.
"""
import mlflow


def log_retrieval_experiment(config_name: str, params: dict, ragas_scores: dict):
    mlflow.set_experiment("finrag-retrieval")
    with mlflow.start_run(run_name=config_name):
        mlflow.log_params(params)
        mlflow.log_metrics(ragas_scores)
