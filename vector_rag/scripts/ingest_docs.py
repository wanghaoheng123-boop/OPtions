import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Tuple

from vector_rag.sqlite_fts import SQLiteFTSStore


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "vector_rag" / "manifest.json"


def chunk_markdown(text: str) -> Iterator[Tuple[str, str]]:
    lines = text.splitlines()
    section = "root"
    buffer = []
    index = 0
    for line in lines:
        if line.startswith("#"):
            if buffer:
                yield section, "\n".join(buffer).strip()
                buffer = []
                index += 1
            section = line.strip("# ").strip() or f"section_{index}"
            buffer.append(line)
        else:
            buffer.append(line)
    if buffer:
        yield section, "\n".join(buffer).strip()


def chunk_json(value, prefix: str = "root") -> Iterator[Tuple[str, str]]:
    if isinstance(value, list):
        for i, item in enumerate(value):
            yield from chunk_json(item, f"{prefix}[{i}]")
    elif isinstance(value, dict):
        if all(not isinstance(v, (dict, list)) for v in value.values()):
            yield prefix, json.dumps(value, ensure_ascii=True)
        else:
            for key, item in value.items():
                yield from chunk_json(item, f"{prefix}.{key}")
    else:
        yield prefix, json.dumps({prefix: value}, ensure_ascii=True)


def ingest_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    store = SQLiteFTSStore()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    total_inserted = 0

    for doc in manifest.get("documents", []):
        doc_id = doc["doc_id"]
        source_path = doc["source_path"]
        source_type = doc["source_type"]
        domain = doc["domain"]
        abs_path = ROOT / source_path
        if not abs_path.exists():
            doc["ingestion_status"] = "missing_source"
            doc["indexed_chunks"] = 0
            continue

        store.clear_doc(doc_id)
        text = abs_path.read_text(encoding="utf-8", errors="ignore")
        inserted = 0

        if source_type == "markdown":
            chunks = chunk_markdown(text)
        else:
            parsed = json.loads(text)
            chunks = chunk_json(parsed)

        for idx, (section, chunk_text) in enumerate(chunks):
            if not chunk_text.strip():
                continue
            chunk_id = f"{doc_id}__{idx:05d}"
            metadata = {
                "doc_id": doc_id,
                "source_path": source_path,
                "domain": domain,
                "source_type": source_type,
                "artifact_origin": doc.get("artifact_origin"),
                "section_title": section,
            }
            store.insert_chunk(
                doc_id=doc_id,
                chunk_id=chunk_id,
                domain=domain,
                source_path=source_path,
                chunk_text=chunk_text,
                metadata=metadata,
                created_at_utc=now,
            )
            inserted += 1

        total_inserted += inserted
        doc["ingestion_status"] = "indexed"
        doc["indexed_chunks"] = inserted
        doc["indexed_at_utc"] = now

    manifest["embedding_store"] = "sqlite_fts"
    manifest["embedding_model"] = "none"
    manifest["last_indexed_utc"] = now
    manifest["total_indexed_chunks"] = total_inserted
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "total_indexed_chunks": total_inserted,
        "db_path": str(store.db_path),
    }


if __name__ == "__main__":
    result = ingest_manifest()
    print(json.dumps(result, indent=2))
