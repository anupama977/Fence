import json
from datetime import datetime
from pathlib import Path

from policy import enforce


BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs.json"


def load_logs():
    if not LOG_FILE.exists():
        return []

    with LOG_FILE.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_log(entry: dict):
    logs = load_logs()
    logs.append(entry)
    with LOG_FILE.open("w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)


async def run_agent(user_input: str) -> dict:
    print(f"\n[FENCE] Received action: {user_input}")

    result = await enforce(user_input)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": user_input,
        "allowed": result["allowed"],
        "stage": result["stage"],
        "reason": result["reason"],
        "rule": result["rule"],
        "warning": result.get("warning"),
        "suggestion": result.get("suggestion"),
        "explanation": result.get("explanation"),
    }

    save_log(log_entry)

    if result["allowed"]:
        print(f"[FENCE] ALLOWED - {result['reason']}")
    else:
        print(f"[FENCE] BLOCKED at {result['stage']} - {result['reason']}")

    return {
        "action": user_input,
        "allowed": result["allowed"],
        "stage": result["stage"],
        "reason": result["reason"],
        "rule": result["rule"],
        "warning": result.get("warning"),
        "suggestion": result.get("suggestion"),
        "explanation": result.get("explanation"),
        "timestamp": log_entry["timestamp"],
    }
