# Vector RAG Chunking Policy

## Objective
Chunk large reference artifacts for semantic retrieval while preserving quantitative traceability.

## General Rules
1. Keep chunks semantically atomic (single result block, single report subsection, or single table context).
2. Preserve provenance metadata on every chunk:
   - `doc_id`
   - `source_path`
   - `domain`
   - optional `ticker`, `strategy`, `time_window`, `quality_gate`
3. Avoid merging unrelated tickers or strategy regimes into a single chunk.

## JSON Artifacts
- Chunk by top-level records (or ticker objects) rather than fixed-size byte windows.
- For nested structures, keep parent key context in metadata.
- Include scalar metric summaries in chunk text to improve retrieval quality.

## Markdown Reports
- Chunk by heading/subheading boundaries.
- Keep list/table blocks with their immediate heading for context.
- Include section title in chunk metadata (`section_title`).

## Query Routing Hints
- Optimization retrospection: prefer `optimization_results` and `optimization_diagnostics`.
- Methodology or policy lookup: prefer `governance_and_research` and `audit_report`.
