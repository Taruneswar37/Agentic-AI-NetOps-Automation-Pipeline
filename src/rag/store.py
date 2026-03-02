"""
Agentic NetOps — ChromaDB Vector Store Wrapper
Provides initialization, persistence, and query methods around ChromaDB.
"""

from __future__ import annotations

import os
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Singleton client ──
_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "netops_knowledge_base"


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        db_path = os.path.abspath(settings.chroma_db_path)
        os.makedirs(db_path, exist_ok=True)

        _client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client initialized", extra={"action": db_path})
    return _client


def get_collection() -> chromadb.Collection:
    """Get or create the knowledge base collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "NetOps compliance, runbooks, and Ansible references"},
        )
        logger.info(
            "Collection ready",
            extra={"action": COLLECTION_NAME, "status": f"{_collection.count()} docs"},
        )
    return _collection


def add_documents(
    documents: list[str],
    metadatas: list[dict[str, Any]],
    ids: list[str],
    embeddings: list[list[float]] | None = None,
) -> None:
    """
    Add documents to the knowledge base collection.

    Args:
        documents: List of text chunks.
        metadatas: List of metadata dicts (one per document).
        ids: List of unique IDs (one per document).
        embeddings: Optional pre-computed embeddings.
    """
    collection = get_collection()
    if embeddings:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )
    else:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
    logger.info("Documents added", extra={"status": f"{len(documents)} chunks"})


def query_collection(
    query_texts: list[str],
    n_results: int = 5,
    query_embeddings: list[list[float]] | None = None,
) -> dict[str, Any]:
    """
    Query the knowledge base.

    Args:
        query_texts: List of query strings.
        n_results: Number of results to return per query.
        query_embeddings: Optional pre-computed query embeddings.

    Returns:
        ChromaDB query results dict.
    """
    collection = get_collection()
    if query_embeddings:
        return collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
        )
    return collection.query(
        query_texts=query_texts,
        n_results=n_results,
    )


def reset_collection() -> None:
    """Delete and recreate the collection (for re-ingestion)."""
    global _collection
    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Existing collection deleted", extra={"action": COLLECTION_NAME})
    except Exception:
        logger.info("Collection does not exist yet, skipping delete", extra={"action": COLLECTION_NAME})
    _collection = None
