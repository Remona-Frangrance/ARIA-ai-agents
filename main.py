from fastapi import FastAPI
from shared.llm_client import ask_llm
from agents.life_admin.agent import handle_task

app = FastAPI(title = "ARIA - AI Agent System")

@app.get("/")
def root():
    return {"message":"ARIA is alive"}

@app.get("/test-ai")
def test_ai():
    response = ask_llm("Give me one productivity tip in one sentence.")
    return {"tip": response}
    
@app.get("/life-admin")
def life_admin(task: str):
    return {"result": handle_task(task)}