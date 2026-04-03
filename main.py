from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent import run_agent
import uvicorn

app = FastAPI(title="Fence - AI Agent Orchestration Layer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    text: str

@app.get("/")
def serve_ui():
    return FileResponse("index.html")

@app.post("/run")
async def run(input: UserInput):
    result = await run_agent(input.text)
    return result

@app.get("/logs")
def get_logs():
    try:
        with open("logs.json", "r") as f:
            import json
            return json.load(f)
    except:
        return []
    
from policy import load_rules, load_sebi_rules, save_rules

@app.get("/config")
def get_config():
    return load_rules()

@app.get("/sebi")
def get_sebi():
    return load_sebi_rules()

class ConfigUpdate(BaseModel):
    goal: str
    rules: list

@app.post("/update-config")
def update_config(config: ConfigUpdate):
    save_rules({"goal": config.goal, "rules": config.rules})
    return {"status": "saved"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)