import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = BASE_DIR / "index.html"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agent import run_agent
from policy import load_rules, load_sebi_rules, save_rules

app = FastAPI(title="Fence - AI Agent Orchestration Layer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserInput(BaseModel):
    text: str


class ConfigUpdate(BaseModel):
    goal: str
    rules: list


@app.get("/")
def serve_ui():
    return FileResponse(INDEX_PATH)


@app.post("/run")
async def run(input: UserInput):
    return await run_agent(input.text)


@app.get("/logs")
def get_logs():
    log_path = BASE_DIR / "logs.json"
    try:
        with log_path.open("r", encoding="utf-8") as f:
            import json

            return json.load(f)
    except Exception:
        return []


@app.get("/config")
def get_config():
    return load_rules()


@app.get("/sebi")
def get_sebi():
    return load_sebi_rules()


@app.post("/update-config")
def update_config(config: ConfigUpdate):
    save_rules({"goal": config.goal, "rules": config.rules})
    return {"status": "saved"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
