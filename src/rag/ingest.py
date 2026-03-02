"""
Agentic NetOps — RAG Document Ingestion Pipeline
Loads markdown documents from knowledge_base/, chunks them,
embeds with a HuggingFace model, and stores in ChromaDB.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import settings
from src.rag.store import add_documents, reset_collection, get_collection
from src.utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

# ── Constants ──
KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"
CHUNK_SIZE = 512          # characters per chunk
CHUNK_OVERLAP = 50        # overlap between chunks


def load_documents(base_dir: Path | None = None) -> list[dict]:
    """
    Load all markdown documents from the knowledge base directory.

    Args:
        base_dir: Override directory (default: project knowledge_base/).

    Returns:
        List of dicts with 'content', 'filename', 'category', and 'path'.
    """
    base = base_dir or KNOWLEDGE_BASE_DIR
    documents = []

    if not base.exists():
        logger.warning("Knowledge base directory not found", extra={"action": str(base)})
        return documents

    for md_file in sorted(base.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        category = md_file.parent.name  # e.g., "compliance_policies"
        documents.append({
            "content": content,
            "filename": md_file.name,
            "category": category,
            "path": str(md_file),
        })

    logger.info("Documents loaded", extra={"status": f"{len(documents)} files"})
    return documents


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The text to split.
        chunk_size: Maximum characters per chunk.
        overlap: Character overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def generate_chunk_id(filename: str, chunk_index: int) -> str:
    """Generate a deterministic ID for a chunk."""
    raw = f"{filename}::chunk_{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def compute_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Compute embeddings for a list of texts using a HuggingFace model.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(settings.embedding_model)
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def ingest(reset: bool = True) -> int:
    """
    Run the full ingestion pipeline.

    Args:
        reset: If True, clear existing data before ingesting.

    Returns:
        Number of chunks ingested.
    """
    console.print("\n[bold cyan]📚 Knowledge Base Ingestion[/bold cyan]\n")

    if reset:
        console.print("[dim]  Resetting existing collection...[/dim]")
        reset_collection()

    # Step 1: Load documents
    documents = load_documents()
    if not documents:
        console.print("[bold red]✗ No documents found in knowledge_base/[/bold red]")
        return 0

    console.print(f"[green]  ✓ Loaded {len(documents)} documents[/green]")

    # Step 2: Chunk all documents
    all_chunks = []
    all_metadatas = []
    all_ids = []

    for doc in documents:
        chunks = chunk_text(doc["content"])
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "filename": doc["filename"],
                "category": doc["category"],
                "chunk_index": i,
                "source_path": doc["path"],
            })
            all_ids.append(generate_chunk_id(doc["filename"], i))

    console.print(f"[green]  ✓ Created {len(all_chunks)} chunks[/green]")

    # Step 3: Compute embeddings
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("  Computing embeddings...", total=None)
        embeddings = compute_embeddings(all_chunks)
        progress.advance(task)

    console.print(f"[green]  ✓ Computed {len(embeddings)} embeddings[/green]")

    # Step 4: Store in ChromaDB
    # ChromaDB has a batch limit — process in batches of 100
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch_end = min(i + batch_size, len(all_chunks))
        add_documents(
            documents=all_chunks[i:batch_end],
            metadatas=all_metadatas[i:batch_end],
            ids=all_ids[i:batch_end],
            embeddings=embeddings[i:batch_end],
        )

    total = get_collection().count()
    console.print(f"\n[bold green]✓ Ingestion complete — {total} chunks in vector store[/bold green]\n")

    return total


if __name__ == "__main__":
    ingest()
