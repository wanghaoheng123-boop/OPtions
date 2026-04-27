import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def check_openviking_inventory() -> list[str]:
    issues = []
    inventory_path = ROOT / "openviking" / "memory_migration_inventory.md"
    if not inventory_path.exists():
        issues.append("Missing openviking inventory file.")
    return issues


def check_graph_schema_edges() -> list[str]:
    issues = []
    schema_path = ROOT / "memory_graph" / "schema.json"
    nodes_path = ROOT / "memory_graph" / "nodes.jsonl"
    edges_path = ROOT / "memory_graph" / "edges.jsonl"
    if not (schema_path.exists() and nodes_path.exists() and edges_path.exists()):
        return ["Missing one or more memory_graph artifacts."]

    schema = _load_json(schema_path)
    nodes = _load_jsonl(nodes_path)
    edges = _load_jsonl(edges_path)
    node_type_by_id = {n["id"]: n["type"] for n in nodes}
    allowed_sources = schema.get("edge_types", {})

    for edge in edges:
        src_id = edge.get("source")
        rel = edge.get("relation")
        dst_id = edge.get("target")
        if src_id not in node_type_by_id:
            issues.append(f"Edge {edge.get('id')} has unknown source node: {src_id}")
            continue
        if dst_id not in node_type_by_id:
            issues.append(f"Edge {edge.get('id')} has unknown target node: {dst_id}")
            continue
        src_type = node_type_by_id[src_id]
        allowed = allowed_sources.get(rel)
        if not allowed:
            issues.append(f"Edge {edge.get('id')} uses unknown relation: {rel}")
            continue
        if src_type not in allowed:
            issues.append(f"Edge {edge.get('id')} source type {src_type} not allowed for relation {rel}")
    return issues


def check_episodic_schema() -> list[str]:
    issues = []
    db_path = ROOT / "episodic_state" / "episodes.db"
    required_tables = {
        "optimization_episode",
        "walk_forward_window_episode",
        "ticker_backtest_episode",
        "validation_gate_episode",
        "failure_constraint_registry",
    }
    if not db_path.exists():
        return ["Missing episodic_state/episodes.db."]

    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()

    missing = required_tables - tables
    for t in sorted(missing):
        issues.append(f"Missing episodic table: {t}")
    return issues


def check_vector_metadata() -> list[str]:
    issues = []
    manifest_path = ROOT / "vector_rag" / "manifest.json"
    taxonomy_path = ROOT / "vector_rag" / "metadata" / "taxonomy.json"
    if not (manifest_path.exists() and taxonomy_path.exists()):
        return ["Missing vector_rag manifest or taxonomy."]

    manifest = _load_json(manifest_path)
    taxonomy = _load_json(taxonomy_path)
    required_tags = set(taxonomy.get("required_tags", []))

    for doc in manifest.get("documents", []):
        missing = [k for k in required_tags if k not in doc]
        if missing:
            issues.append(f"Document {doc.get('doc_id', '<unknown>')} missing required tags: {', '.join(sorted(missing))}")
    return issues


def main() -> int:
    checks = [
        ("OpenViking inventory", check_openviking_inventory),
        ("Graph schema/edges", check_graph_schema_edges),
        ("Episodic schema", check_episodic_schema),
        ("Vector metadata", check_vector_metadata),
    ]

    all_issues: list[str] = []
    for name, fn in checks:
        issues = fn()
        if issues:
            print(f"[FAIL] {name}")
            for i in issues:
                print(f"  - {i}")
            all_issues.extend(issues)
        else:
            print(f"[PASS] {name}")

    if all_issues:
        print(f"\nMemory consistency check failed: {len(all_issues)} issue(s).")
        return 1
    print("\nMemory consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
