"""ChromaDB CRUD wrapper with metadata filtering."""
import chromadb
from loguru import logger


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "finrag"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)

    def add(self, ids: list, texts: list, embeddings: list, metadatas: list):
        self.collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        logger.info(f"Added {len(ids)} chunks to vector store")

    def query(self, embedding: list, top_k: int = 5, where: dict = None):
        results = self.collection.query(
            query_embeddings=[embedding], n_results=top_k, where=where
        )
        return results

    def count(self):
        return self.collection.count()
