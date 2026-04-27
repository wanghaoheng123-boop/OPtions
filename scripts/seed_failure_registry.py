import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TICKER_RESULTS_PATH = ROOT / "review" / "SECTOR_DEEP_DIVE" / "TICKER_RESULTS.json"
EPISODIC_DB_PATH = ROOT / "episodic_state" / "episodes.db"


def stable_hash(payload: dict) -> str:
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()


def failure_signature_hash(
    ticker: str,
    strategy_type: str,
    tp: float,
    sl: float,
    t_hor: int,
    ewma_span: int,
    reason: str,
) -> str:
    return stable_hash(
        {
            "ticker": ticker.upper(),
            "strategy_type": strategy_type,
            "tp": tp,
            "sl": sl,
            "t_hor": t_hor,
            "ewma_span": ewma_span,
            "reason": reason,
        }
    )


def infer_constraint_reason(row: dict) -> str:
    win_rate = float(row.get("win_rate_percent") or 0.0)
    pf = float(row.get("profit_factor") or 0.0)
    max_dd = float(row.get("max_drawdown_percent") or 0.0)
    reasons = []
    if win_rate < 75.0:
        reasons.append(f"win_rate_below_gate:{win_rate:.2f}")
    if pf < 1.2:
        reasons.append(f"profit_factor_below_gate:{pf:.2f}")
    if max_dd >= 20.0:
        reasons.append(f"drawdown_above_gate:{max_dd:.2f}")
    if not reasons:
        verdict = str(row.get("verdict", "FAIL"))
        reasons.append(f"verdict:{verdict.lower()}")
    return "|".join(reasons)


def seed_failure_registry() -> int:
    if not TICKER_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Missing ticker results file: {TICKER_RESULTS_PATH}")
    if not EPISODIC_DB_PATH.exists():
        raise FileNotFoundError(f"Missing episodic db: {EPISODIC_DB_PATH}")

    data = json.loads(TICKER_RESULTS_PATH.read_text(encoding="utf-8"))
    fail_rows = [row for row in data if str(row.get("verdict", "")).upper() == "FAIL"]

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    inserted = 0
    updated = 0

    with sqlite3.connect(EPISODIC_DB_PATH) as conn:
        for row in fail_rows:
            ticker = str(row.get("ticker", "")).upper()
            strategy_type = "iron_condor"

            # TICKER_RESULTS does not include full optimizer tuples.
            # Use canonical defaults and keep full row in failure_context_json.
            tp = 0.5
            sl = 1.5
            t_hor = 5
            ewma_span = 20
            reason = infer_constraint_reason(row)

            signature = failure_signature_hash(
                ticker=ticker,
                strategy_type=strategy_type,
                tp=tp,
                sl=sl,
                t_hor=t_hor,
                ewma_span=ewma_span,
                reason=reason,
            )

            context = {
                "source": "review/SECTOR_DEEP_DIVE/TICKER_RESULTS.json",
                "seeded_from_historical_review": True,
                "ticker_result": row,
                "assumed_optimizer_tuple": {
                    "tp": tp,
                    "sl": sl,
                    "t_hor": t_hor,
                    "ewma_span": ewma_span,
                },
            }

            exists = conn.execute(
                "SELECT 1 FROM failure_constraint_registry WHERE failed_signature_hash = ? LIMIT 1",
                (signature,),
            ).fetchone()

            conn.execute(
                """
                INSERT INTO failure_constraint_registry (
                  failed_signature_hash, first_seen_utc, last_seen_utc, strategy_type, ticker,
                  constraint_class, constraint_detail, failure_context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(failed_signature_hash) DO UPDATE SET
                  last_seen_utc=excluded.last_seen_utc,
                  constraint_detail=excluded.constraint_detail,
                  failure_context_json=excluded.failure_context_json
                """,
                (
                    signature,
                    now,
                    now,
                    strategy_type,
                    ticker,
                    "historical_backtest_gate",
                    reason,
                    json.dumps(context, sort_keys=True),
                ),
            )

            if exists:
                updated += 1
            else:
                inserted += 1

        conn.commit()

    print(
        json.dumps(
            {
                "seeded_failures": len(fail_rows),
                "inserted": inserted,
                "updated": updated,
                "db_path": str(EPISODIC_DB_PATH),
            },
            indent=2,
        )
    )
    return inserted


if __name__ == "__main__":
    seed_failure_registry()
