from chunking.text_chunker import chunk_text


def chunk_email(email_dict: dict) -> list:
    """One chunk per email if it fits the size, else split with email-sized config."""
    return chunk_text(email_dict["text"], doc_type="email")
