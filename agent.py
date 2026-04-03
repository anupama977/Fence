import json
import os
from datetime import datetime
from policy import enforce

LOG_FILE = "logs.json"

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def save_log(entry: dict):
    logs = load_logs()
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

async def run_agent(user_input: str) -> dict:
    print(f"\n[FENCE] Received action: {user_input}")

    # run through the full fence pipeline
    result = await enforce(user_input)

    # build the log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": user_input,
        "allowed": result["allowed"],
        "stage": result["stage"],
        "reason": result["reason"],
        "rule": result["rule"]
    }

    # save to logs
    save_log(log_entry)

    # print to terminal so you can see whats happening
    if result["allowed"]:
        print(f"[FENCE] ALLOWED — {result['reason']}")
    else:
        print(f"[FENCE] BLOCKED at {result['stage']} — {result['reason']}")

    return {
        "action": user_input,
        "allowed": result["allowed"],
        "stage": result["stage"],
        "reason": result["reason"],
        "rule": result["rule"],
        "timestamp": log_entry["timestamp"]
    }