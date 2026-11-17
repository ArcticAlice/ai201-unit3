"""
Structured logger for FitFindr Capstone.
Records every execution to a JSON Lines log file with named fields:
timestamp, run_id, action, input, output, duration_sec, tokens, and estimated cost.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOGS_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOGS_DIR / "session_runs.jsonl"


def log_run(
    action: str,
    inputs: dict,
    outputs: dict,
    duration_sec: float,
    tokens: dict,
    status: str = "success",
    error_or_warning: str | None = None,
) -> dict:
    """
    Append one structured log record to logs/session_runs.jsonl.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Gemini 2.5/3.5 Flash Lite Pricing reference:
    # Prompt: $0.075 / 1M tokens ($0.000000075 / token)
    # Output: $0.30 / 1M tokens ($0.00000030 / token)
    prompt_tokens = tokens.get("prompt", 0)
    output_tokens = tokens.get("output", 0)
    total_tokens = tokens.get("total", prompt_tokens + output_tokens)
    cost_usd = (prompt_tokens * 0.000000075) + (output_tokens * 0.00000030)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": str(uuid.uuid4())[:8],
        "action": action,
        "status": status,
        "input": inputs,
        "output": outputs,
        "duration_sec": round(duration_sec, 4),
        "tokens": {
            "prompt": prompt_tokens,
            "output": output_tokens,
            "total": total_tokens,
        },
        "cost_usd": round(cost_usd, 7),
        "error_or_warning": error_or_warning,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return record


def read_logs(limit: int = 15) -> list[dict]:
    """Read the latest log records."""
    if not LOG_FILE.exists():
        return []
    records = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    return records[-limit:]
