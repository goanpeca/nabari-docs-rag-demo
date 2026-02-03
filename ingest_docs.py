#!/usr/bin/env python3
"""Document ingestion pipeline for Nebari documentation.

Scans the nebari-docs directory, chunks markdown files semantically,
generates embeddings, and stores them in ChromaDB.
"""

import argparse
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from utils.chunking import chunk_by_headers, extract_frontmatter, strip_mdx_components

# Load environment variables
load_dotenv()


def scan_docs_directory(docs_path: str) -> list[dict[str, Any]]:
    """Scan nebari-docs directory recursively for markdown files.

    Parameters
    ----------
    docs_path : str
        Path to nebari-docs repository

    Returns
    -------
    list[dict[str, Any]]
        List of document dictionaries with content and metadata
    """
    docs: list[dict[str, Any]] = []
    docs_dir = Path(docs_path) / "docs" / "docs"

    if not docs_dir.exists():
        print(f" Documentation directory not found: {docs_dir}")
        return docs

    # Find all .md and .mdx files
    md_files = list(docs_dir.glob("**/*.md"))
    mdx_files = list(docs_dir.glob("**/*.mdx"))
    all_files = md_files + mdx_files

    print(f" Found {len(all_files)} documentation files")

    for file_path in all_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Extract frontmatter
            frontmatter, content = extract_frontmatter(content)

            # Strip MDX components if it's an MDX file
            if file_path.suffix == ".mdx":
                content = strip_mdx_components(content)

            # Determine category from path
            relative_path = file_path.relative_to(docs_dir)
            category = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"

            # Build metadata
            metadata = {
                "file_path": str(relative_path),
                "category": category,
                "title": frontmatter.get("title", file_path.stem),
                "description": frontmatter.get("description", ""),
                "id": frontmatter.get("id", file_path.stem),
                "source_file": str(file_path),
            }

            docs.append({"content": content, "metadata": metadata})

        except (OSError, UnicodeDecodeError) as e:
            print(f"  Error processing {file_path}: {e}")

    return docs


def chunk_documents(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chunk documents semantically by headers.

    Parameters
    ----------
    docs : list[dict[str, Any]]
        List of documents with content and metadata

    Returns
    -------
    list[dict[str, Any]]
        List of chunks with text and enriched metadata
    """
    all_chunks: list[dict[str, Any]] = []

    for doc in docs:
        chunks = chunk_by_headers(doc["content"], doc["metadata"], max_chunk_size=800, overlap=100)

        for chunk_text, chunk_metadata in chunks:
            all_chunks.append({"text": chunk_text, "metadata": chunk_metadata})

    print(f"  Created {len(all_chunks)} chunks from {len(docs)} documents")
    return all_chunks


def ingest_to_chroma(
    chunks: list[dict[str, Any]],
    collection_name: str = "nebari_docs",
    persist_directory: str = "./chroma_db",
) -> None:
    """Generate embeddings and store chunks in ChromaDB.

    Parameters
    ----------
    chunks : list[dict[str, Any]]
        List of chunk dictionaries
    collection_name : str, default "nebari_docs"
        Name of Chroma collection
    persist_directory : str, default "./chroma_db"
        Directory to persist the database
    """
    print("\n Initializing ChromaDB...")

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )

    # Delete existing collection if it exists
    try:
        client.delete_collection(name=collection_name)
        print(f"  Deleted existing collection: {collection_name}")
    except ValueError:
        # Collection doesn't exist, which is fine
        print(f"  No existing collection to delete: {collection_name}")

    # Create new collection
    # Using default embedding function (all-MiniLM-L6-v2)
    collection = client.create_collection(
        name=collection_name, metadata={"description": "Nebari documentation chunks"}
    )

    # Prepare data for ingestion
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    # Add to collection in batches
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_metadatas = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]

        collection.add(documents=batch_texts, metadatas=batch_metadatas, ids=batch_ids)

        print(f"   Ingested batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

    print(f"\n Successfully ingested {len(chunks)} chunks to ChromaDB")
    print(f" Database location: {persist_directory}")


def main() -> None:
    """Run the documentation ingestion pipeline."""
    parser = argparse.ArgumentParser(description="Ingest Nebari documentation into ChromaDB")
    parser.add_argument(
        "--docs-path",
        type=str,
        default=os.getenv("NEBARI_DOCS_PATH", "../nebari-docs"),
        help="Path to nebari-docs repository",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
        help="Directory to persist ChromaDB",
    )
    parser.add_argument(
        "--force-refresh", action="store_true", help="Force refresh of the database"
    )

    args = parser.parse_args()

    print(" Nebari Documentation Ingestion Pipeline")
    print("=" * 50)

    # Step 1: Scan documents
    print(f"\n Scanning documents from: {args.docs_path}")
    docs = scan_docs_directory(args.docs_path)

    if not docs:
        print(" No documents found. Check the path.")
        return

    # Step 2: Chunk documents
    print("\n  Chunking documents...")
    chunks = chunk_documents(docs)

    # Step 3: Ingest to ChromaDB
    ingest_to_chroma(chunks, persist_directory=args.persist_dir)

    print("\n" + "=" * 50)
    print(" Ingestion complete!")
    print("\n Summary:")
    print(f"   • Documents processed: {len(docs)}")
    print(f"   • Chunks created: {len(chunks)}")
    print(f"   • Database location: {args.persist_dir}")


if __name__ == "__main__":
    main()
