# FinRAG — Stage 1 + 2 + 3 — Colab Run Guide

Stage 3 adds: Redis semantic cache, Prometheus metrics, and a live dashboard
at /dashboard -- all running inside this same Colab session. Grafana, Airflow,
DVC, and MLflow are delivered as real code (matching the project spec) but are
meant for the Stage 4 Docker deployment, not this notebook -- installing full
Airflow/Grafana servers alongside everything else here is exactly the kind of
thing that caused the dependency conflicts you already hit. Keeping them out
of Colab keeps this environment stable.

## 0. Get two free API keys (if you haven't already)
- Groq: https://console.groq.com/keys
- Gemini: https://aistudio.google.com/app/apikey

## 1. New Colab notebook, T4 runtime
Runtime -> Change runtime type -> T4 GPU -> Save.

## 2. Cell 1 -- Mount Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```

## 3. Cell 2 -- Upload finrag.zip, unzip
```python
!rm -rf /content/finrag
!unzip -q /content/finrag.zip -d /content/
%cd /content/finrag
```

## 4. Cell 3 -- System deps (now includes Redis server)
```python
!apt-get -qq install -y poppler-utils libmagic1 redis-server
```

## 5. Cell 4 -- Start Redis in the background
```python
!redis-server --daemonize yes
!redis-cli ping   # should print PONG
```

## 6. Cell 5 -- Python deps
```python
!pip install -q -r requirements.txt
```

## 7. Runtime -> Restart session
(Still required after installing/upgrading packages -- same reason as before.)
After restarting, re-run Cells 1-4 (mount, unzip, apt installs, start Redis)
-- installed pip packages persist on disk so you don't need to redo Cell 5.

## 8. Cell 6 -- Set environment variables
```python
import os
os.environ["GROQ_API_KEY"] = "paste_your_groq_key_here"
os.environ["GOOGLE_API_KEY"] = "paste_your_gemini_key_here"
os.environ["CHROMA_PERSIST_DIR"] = "/content/drive/MyDrive/finrag/chromadb"
os.environ["SQLITE_PATH"] = "/content/drive/MyDrive/finrag/tables.db"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.makedirs("/content/drive/MyDrive/finrag", exist_ok=True)
```

## 9. Cell 7 -- Start the API + UI
```python
!python colab_stage1_setup.py
```
Click the gradio.live link it prints.

## 10. What's new to try
- Ask the **same question twice** -- the second time should return almost
  instantly (cache hit, tier/model shown will match the first answer, tokens
  used will be 0 since no generation happened).
- Open the live dashboard directly in your browser: append `/dashboard` to
  wherever the API is reachable. On Colab, the API itself isn't tunneled by
  default (only Gradio is) -- easiest way to see it: in a new cell:
  ```python
  import requests
  print(requests.get("http://localhost:8000/metrics").json())
  ```
  If you want the actual visual dashboard, you can tunnel port 8000 too:
  ```python
  from pyngrok import ngrok
  public_url = ngrok.connect(8000)
  print(public_url)
  ```
  (Needs a free ngrok account + authtoken: https://dashboard.ngrok.com/get-started/your-authtoken,
  then `!ngrok config add-authtoken YOUR_TOKEN` once before connecting.)
  Then visit `<that ngrok url>/dashboard`.
- Raw Prometheus metrics (text format, what a real Prometheus server would
  scrape): `http://localhost:8000/metrics/prometheus`.

## 11. If Redis isn't running
The cache fails soft -- if Redis is down, `/query` just skips caching and
works exactly like Stage 2 (no crash). Check with `!redis-cli ping`; if it
doesn't say PONG, re-run `!redis-server --daemonize yes`.

## 12. Where things are stored
Same as before -- `/content/drive/MyDrive/finrag/`. Redis cache itself is
in-memory only and does NOT persist across Colab restarts (that's expected
and fine -- it's a cache, not a database).

## What's delivered as code but not run here (Stage 4 Docker)
- `monitoring/grafana_dashboards/*.json` -- real Grafana panel configs
- `orchestration/airflow_dags/*.py` -- real Airflow DAGs
- `dvc.yaml` -- DVC pipeline definition
- `experiments/mlflow_logging.py` -- MLflow experiment tracking (local file-based,
  actually usable if you want to try it standalone: `pip install mlflow` and
  call `log_retrieval_experiment(...)`, but not wired into the live API)

These become real running services in Stage 4's docker-compose stack, isolated
in their own containers so they can't conflict with the RAG app's Python deps.
