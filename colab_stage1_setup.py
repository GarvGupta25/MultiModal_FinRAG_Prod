"""
Run this in a Colab cell to install deps and start Stage 1 (API + UI) in the background.
See README_COLAB.md for the full step-by-step.
"""
import os
import subprocess
import time
import threading
import nest_asyncio

nest_asyncio.apply()


def start_api():
    subprocess.Popen(["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])


def start_ui():
    subprocess.Popen(["python", "ui/app.py"])


if __name__ == "__main__":
    start_api()
    time.sleep(8)   # let API boot + load embedding model
    start_ui()
