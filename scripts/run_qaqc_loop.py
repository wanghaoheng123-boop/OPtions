import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "review" / "QAQC"
OUT_DIR.mkdir(parents=True, exist_ok=True)


CHECKS = [
    ["python", "-m", "pytest", "tests/test_smoke_api.py", "-q"],
    ["python", "-m", "pytest", "tests/", "-m", "not network", "-q"],
]


def run_check(cmd: list[str]) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        return {
            "command": " ".join(cmd),
            "started_at": started,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "status": "PASS" if proc.returncode == 0 else "FAIL",
        }
    except Exception as exc:
        return {
            "command": " ".join(cmd),
            "started_at": started,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(exc),
            "status": "FAIL",
        }


def main() -> None:
    results = [run_check(cmd) for cmd in CHECKS]
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL",
        "results": results,
        "qaqc_checklist": {
            "api_contract_transport_errors": "manual review required",
            "ui_display_states": "manual review required",
            "quant_leakage_overfit_gate": "manual review required",
            "residual_risks_logged": "manual review required",
        },
    }
    out_file = OUT_DIR / "latest_qaqc_report.json"
    out_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["overall_status"], "report": str(out_file)}, indent=2))


if __name__ == "__main__":
    main()

