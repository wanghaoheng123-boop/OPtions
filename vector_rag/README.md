# Vector RAG Layer

## Canonical Artifacts
- `vector_rag/manifest.json`
- `vector_rag/metadata/taxonomy.json`
- `vector_rag/chunks/chunking_policy.md`

## Layer Role
Holds heavy and unstructured/semistructured knowledge for similarity retrieval without inflating hot context tokens.

## Retrieval Guidance
- Use this layer for large reports, historical optimization payloads, and external references.
- Do not use as primary source for live execution state; use L0/L1 or episodic SQLite first.
