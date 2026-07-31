"""Gradio UI -- upload a document, ask a question, see the answer + sources."""
import requests
import gradio as gr

API_URL = "http://localhost:8000"


def ingest_file(file):
    if file is None:
        return "No file selected."
    with open(file.name, "rb") as f:
        resp = requests.post(f"{API_URL}/ingest", files={"file": f})

    if resp.status_code != 200:
        return f"Error: {resp.text}"

    data = resp.json()

    return (
        f"Ingested as `{data['document_type']}`\n"
        f"Chunks: {data['chunks_created']}\n"
        f"Time: {data['processing_time_ms']:.0f} ms\n"
        f"Document ID: {data['document_id']}"
    )


def ask_question(query):
    if not query.strip():
        return "Please enter a question.", ""

    resp = requests.post(
        f"{API_URL}/query",
        json={"query": query, "top_k": 5},
    )

    if resp.status_code != 200:
        return f"Error: {resp.text}", ""

    data = resp.json()

    sources = "\n\n".join(
        f"### {s['source']}\n"
        f"Score: {s['score']:.2f}\n\n"
        f"{s['text']}"
        for s in data["sources"]
    )

    meta = (
        f"**Tier:** {data['tier']} | "
        f"**Model:** {data['model_used']} | "
        f"**Tokens:** {data['tokens_used']} | "
        f"**Saved:** {data['tokens_saved_vs_tier3']} | "
        f"**Latency:** {data['total_latency_ms']:.0f} ms"
    )

    return f"{data['answer']}\n\n---\n{meta}", sources


# -------------------------
# Dashboard
# -------------------------

def load_dashboard():
    try:
        return requests.get(f"{API_URL}/dashboard").text
    except Exception as e:
        return f"<h2>Error loading dashboard</h2><pre>{e}</pre>"


# -------------------------
# Metrics
# -------------------------

def load_metrics():
    try:
        return requests.get(f"{API_URL}/metrics").json()
    except Exception as e:
        return {"error": str(e)}


# -------------------------
# Health
# -------------------------

def load_health():
    try:
        return requests.get(f"{API_URL}/health").json()
    except Exception as e:
        return {"error": str(e)}


with gr.Blocks(title="FinRAG") as demo:

    gr.Markdown("# 📄 FinRAG")
    gr.Markdown("### Financial Document Question Answering System")

    # ==========================
    # Upload
    # ==========================

    with gr.Tab("📄 Upload"):

        file_input = gr.File(
            label="Upload PDF / Image / TXT / Email"
        )

        ingest_btn = gr.Button("Ingest Document")

        ingest_output = gr.Textbox(
            label="Status",
            lines=5
        )

        ingest_btn.click(
            ingest_file,
            inputs=file_input,
            outputs=ingest_output
        )

    # ==========================
    # Chat
    # ==========================

    with gr.Tab("💬 Chat"):

        query_input = gr.Textbox(
            label="Ask a Question"
        )

        ask_btn = gr.Button("Ask")

        answer_output = gr.Markdown()

        sources_output = gr.Markdown()

        ask_btn.click(
            ask_question,
            inputs=query_input,
            outputs=[answer_output, sources_output]
        )

    # ==========================
    # Dashboard
    # ==========================

    with gr.Tab("📊 Dashboard"):

        dashboard = gr.HTML()

        refresh_dashboard = gr.Button("Refresh Dashboard")

        refresh_dashboard.click(
            load_dashboard,
            outputs=dashboard
        )

        demo.load(
            load_dashboard,
            outputs=dashboard
        )

    # ==========================
    # Metrics
    # ==========================

    with gr.Tab("📈 Metrics"):

        metrics = gr.JSON()

        refresh_metrics = gr.Button("Refresh Metrics")

        refresh_metrics.click(
            load_metrics,
            outputs=metrics
        )

        demo.load(
            load_metrics,
            outputs=metrics
        )

    # ==========================
    # Health
    # ==========================

    with gr.Tab("❤️ Health"):

        health = gr.JSON()

        refresh_health = gr.Button("Refresh Health")

        refresh_health.click(
            load_health,
            outputs=health
        )

        demo.load(
            load_health,
            outputs=health
        )


if __name__ == "__main__":
    demo.launch(share=True)