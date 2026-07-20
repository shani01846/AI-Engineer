import os
from dotenv import load_dotenv
from google import genai

from task_service import (
    add_task,
    get_tasks,
    update_task,
    delete_task
)


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


SYSTEM_PROMPT = """
You are an AI task management assistant.

Your job is to help the user manage tasks.

You have access to tools:
- add_task: create a new task
- get_tasks: retrieve existing tasks
- update_task: modify an existing task
- delete_task: remove a task

Rules:
1. Always use tools when the user wants to create, update, delete or retrieve tasks.
2. Never invent task data,Do not invent user-provided task details. If the user says relative dates like today or tomorrow, convert them to actual dates.
3. If required information is missing, ask the user for it.
4. Dates should be returned in YYYY-MM-DD format.
5. After executing a tool, explain the result clearly and briefly.
"""


def agent(query: str):

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=query,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "tools": [
                add_task,
                get_tasks,
                update_task,
                delete_task
            ]
        }
    )
    print(response)   # ← כאן

    return response