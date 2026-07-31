"""Loads a single .eml file into plain text. IMAP fetching is a thin add-on (MCP-ready)."""
from email import policy
from email.parser import BytesParser
from loguru import logger


def load_eml(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content()

    text = (
        f"From: {msg['from']}\nTo: {msg['to']}\nSubject: {msg['subject']}\n"
        f"Date: {msg['date']}\n\n{body}"
    )
    logger.info(f"Loaded email: {file_path}")
    return {"text": text, "subject": msg["subject"], "from": msg["from"], "date": msg["date"]}


def fetch_via_imap(host: str, user: str, password: str, mailbox: str = "INBOX", limit: int = 10) -> list:
    """Minimal IMAP fetch, kept simple so it can later be swapped for an MCP email connector."""
    import imaplib
    conn = imaplib.IMAP4_SSL(host)
    conn.login(user, password)
    conn.select(mailbox)
    _, data = conn.search(None, "ALL")
    ids = data[0].split()[-limit:]
    emails = []
    for eid in ids:
        _, msg_data = conn.fetch(eid, "(RFC822)")
        raw = msg_data[0][1]
        msg = BytesParser(policy=policy.default).parsebytes(raw)
        body = msg.get_body(preferencelist=("plain",))
        text = body.get_content() if body else ""
        emails.append({"text": text, "subject": msg["subject"], "from": msg["from"], "date": msg["date"]})
    conn.logout()
    return emails
