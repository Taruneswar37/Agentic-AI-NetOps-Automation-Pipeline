"""
Agentic NetOps — RAG Query Interface
Provides a clean interface for agents to query the knowledge base.
"""

from __future__ import annotations

from src.rag.store import query_collection, get_collection
from src.rag.ingest import compute_embeddings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def query_knowledge_base(
    question: str,
    top_k: int = 5,
    category_filter: str | None = None,
) -> str:
    """
    Query the RAG knowledge base and return formatted context.

    This is the primary interface used by all agents for:
    - Compliance policy lookups (Planner)
    - Ansible syntax references (Coder)

    Args:
        question: Natural language question.
        top_k: Number of results to retrieve.
        category_filter: Optional filter by document category
                         (e.g., "compliance_policies", "runbooks", "ansible_references").

    Returns:
        Formatted string containing the top-k relevant passages
        with source metadata.
    """
    collection = get_collection()

    # Check if collection is empty
    if collection.count() == 0:
        logger.warning("Knowledge base is empty — run ingestion first")
        return "[Knowledge base is empty. Run: python src/rag/ingest.py]"

    # Compute embedding for the query
    query_embedding = compute_embeddings([question])

    # Build where clause for category filtering
    where_filter = None
    if category_filter:
        where_filter = {"category": category_filter}

    # Query ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_filter,
    )

    # Format results
    if not results or not results.get("documents") or not results["documents"][0]:
        return "[No relevant documents found in knowledge base]"

    formatted_chunks = []
    for i, (doc, meta) in enumerate(
        zip(results["documents"][0], results["metadatas"][0])
    ):
        source = meta.get("filename", "unknown")
        category = meta.get("category", "unknown")
        formatted_chunks.append(
            f"--- Source: {source} ({category}) ---\n{doc}"
        )

    context = "\n\n".join(formatted_chunks)

    logger.info(
        "RAG query completed",
        extra={"status": f"{len(formatted_chunks)} results"},
    )
    return context


def query_compliance(question: str, top_k: int = 3) -> str:
    """Convenience function for compliance policy lookups."""
    return query_knowledge_base(
        question=question,
        top_k=top_k,
        category_filter="compliance_policies",
    )


def query_ansible_syntax(question: str, top_k: int = 3) -> str:
    """Convenience function for Ansible module syntax lookups."""
    return query_knowledge_base(
        question=question,
        top_k=top_k,
        category_filter="ansible_references",
    )


def query_runbook(question: str, top_k: int = 3) -> str:
    """Convenience function for device runbook lookups."""
    return query_knowledge_base(
        question=question,
        top_k=top_k,
        category_filter="runbooks",
    )
