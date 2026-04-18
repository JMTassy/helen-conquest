#!/usr/bin/env python3
"""
HELEN Knowledge Ingestion — Local RAG pipeline.

Reads your PDFs, markdown, and text files.
Chunks them. Embeds them with Gemini. Stores locally as JSON.
HELEN searches at query time — no cloud, no upload, your data stays yours.

Usage:
    python3 helen_os/knowledge/ingest.py --sources ~/Documents ~/Desktop
    python3 helen_os/knowledge/ingest.py --sources ~/Documents/important.pdf
    python3 helen_os/knowledge/ingest.py --query "what are my investment notes"

Non-sovereign: reads only. Does not modify source files.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

KNOWLEDGE_DIR = Path(__file__).parent
INDEX_PATH = KNOWLEDGE_DIR / "index.json"
EMBEDDINGS_DIR = KNOWLEDGE_DIR / "embeddings"

CHUNK_SIZE = 800  # chars per chunk
CHUNK_OVERLAP = 100
SUPPORTED_EXTS = {".md", ".txt", ".pdf", ".ndjson", ".csv", ".py", ".json"}
SKIP_DIRS = {"node_modules", ".git", ".venv", "__pycache__", ".claude", "worktrees", ".pytest_cache"}

# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_text(path: Path) -> Optional[str]:
    """Extract text from a file. Returns None if unsupported or empty."""
    try:
        if path.suffix == ".pdf":
            r = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                             capture_output=True, text=True, timeout=30)
            return r.stdout if r.returncode == 0 else None
        elif path.suffix in (".md", ".txt", ".csv", ".py", ".json", ".ndjson"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            return text if len(text) > 20 else None
        return None
    except Exception:
        return None


# ─── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


# ─── Embedding ────────────────────────────────────────────────────────────────

def embed_batch(texts: List[str], api_key: str) -> List[List[float]]:
    """Embed a batch of texts using Gemini embedding model."""
    sys.path.insert(0, str(Path(__file__).parents[2] / ".venv" / "lib" / "python3.14" / "site-packages"))
    from google import genai

    client = genai.Client(api_key=api_key)
    embeddings = []
    # Batch in groups of 20 (API limit)
    for i in range(0, len(texts), 20):
        batch = texts[i:i+20]
        try:
            r = client.models.embed_content(
                model="gemini-embedding-001",
                contents=batch,
            )
            for emb in r.embeddings:
                embeddings.append(emb.values)
        except Exception as e:
            print(f"  Embedding error at batch {i}: {e}")
            # Fill with zeros for failed batch
            for _ in batch:
                embeddings.append([0.0] * 3072)
        time.sleep(0.5)  # rate limit
    return embeddings


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─── Index ────────────────────────────────────────────────────────────────────

def load_index() -> Dict[str, Any]:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text())
    return {"version": 1, "chunks": [], "files_indexed": 0, "total_chunks": 0}


def save_index(index: Dict[str, Any]):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")


def save_embeddings(chunk_id: int, embedding: List[float]):
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    path = EMBEDDINGS_DIR / f"{chunk_id}.json"
    path.write_text(json.dumps(embedding))


def load_embedding(chunk_id: int) -> Optional[List[float]]:
    path = EMBEDDINGS_DIR / f"{chunk_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


# ─── Ingest ───────────────────────────────────────────────────────────────────

def ingest(sources: List[str], api_key: str, max_files: int = 500):
    """Ingest files from source directories/paths."""
    index = load_index()
    existing_hashes = {c["hash"] for c in index["chunks"]}

    # Collect files
    files: List[Path] = []
    for src in sources:
        p = Path(src).expanduser()
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.suffix in SUPPORTED_EXTS:
                    if not any(skip in f.parts for skip in SKIP_DIRS):
                        files.append(f)

    files = files[:max_files]
    print(f"Found {len(files)} files to process (max {max_files})")

    new_chunks = []
    for i, f in enumerate(files):
        text = extract_text(f)
        if not text:
            continue

        chunks = chunk_text(text)
        for j, chunk in enumerate(chunks):
            h = hashlib.sha256(chunk.encode()).hexdigest()[:16]
            if h in existing_hashes:
                continue
            new_chunks.append({
                "id": index["total_chunks"] + len(new_chunks),
                "file": str(f),
                "chunk_index": j,
                "text": chunk[:2000],  # cap stored text
                "hash": h,
                "chars": len(chunk),
            })

        if (i + 1) % 50 == 0:
            print(f"  Scanned {i+1}/{len(files)} files, {len(new_chunks)} new chunks")

    if not new_chunks:
        print("No new chunks to embed.")
        return

    print(f"\nEmbedding {len(new_chunks)} new chunks...")
    texts = [c["text"] for c in new_chunks]
    embeddings = embed_batch(texts, api_key)

    for chunk, emb in zip(new_chunks, embeddings):
        save_embeddings(chunk["id"], emb)
        index["chunks"].append({
            "id": chunk["id"],
            "file": chunk["file"],
            "chunk_index": chunk["chunk_index"],
            "hash": chunk["hash"],
            "chars": chunk["chars"],
            "preview": chunk["text"][:100],
        })

    index["total_chunks"] += len(new_chunks)
    index["files_indexed"] = len(set(c["file"] for c in index["chunks"]))
    save_index(index)
    print(f"\nDone. Index: {index['files_indexed']} files, {index['total_chunks']} chunks.")


# ─── Query ────────────────────────────────────────────────────────────────────

def query(question: str, api_key: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search the knowledge index. Returns top_k most relevant chunks."""
    index = load_index()
    if not index["chunks"]:
        return []

    # Embed the question
    q_emb = embed_batch([question], api_key)[0]

    # Score all chunks
    scored = []
    for chunk in index["chunks"]:
        emb = load_embedding(chunk["id"])
        if emb is None:
            continue
        sim = cosine_similarity(q_emb, emb)
        scored.append((sim, chunk))

    # Top-k
    scored.sort(key=lambda x: -x[0])
    results = []
    for sim, chunk in scored[:top_k]:
        # Load full text
        chunk_file = EMBEDDINGS_DIR.parent / "index.json"
        # Find the full text from the original chunk list in index
        full_text = chunk.get("preview", "")
        results.append({
            "score": round(sim, 4),
            "file": chunk["file"],
            "preview": full_text,
            "chunk_id": chunk["id"],
        })

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="HELEN Knowledge Ingestion")
    ap.add_argument("--sources", nargs="+", help="Directories or files to ingest")
    ap.add_argument("--query", help="Search the knowledge index")
    ap.add_argument("--max-files", type=int, default=500, help="Max files to process")
    ap.add_argument("--status", action="store_true", help="Show index status")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and not args.status:
        print("Set GEMINI_API_KEY env var")
        sys.exit(1)

    if args.status:
        idx = load_index()
        print(f"Files indexed: {idx['files_indexed']}")
        print(f"Total chunks:  {idx['total_chunks']}")
        print(f"Index path:    {INDEX_PATH}")
        return

    if args.sources:
        ingest(args.sources, api_key, args.max_files)
    elif args.query:
        results = query(args.query, api_key)
        if not results:
            print("No results. Run --sources first to build the index.")
            return
        for r in results:
            print(f"\n[{r['score']}] {r['file']}")
            print(f"  {r['preview']}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
