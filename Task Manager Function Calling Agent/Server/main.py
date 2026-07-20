from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_service import agent
from task_service import get_tasks


app = FastAPI(
    title="Task Manager AI Agent"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {
        "message": "Task Manager Agent is running"
    }


@app.get("/tasks")
def tasks():
    return get_tasks()


@app.post("/chat")
def chat(request: ChatRequest):

    try:
        response = agent(request.message)

        return {
            "response": response.text
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )