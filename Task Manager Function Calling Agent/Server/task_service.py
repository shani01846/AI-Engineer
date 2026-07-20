import json
from pathlib import Path
from typing import Optional

from models import Task


TASKS_FILE = Path("tasks.json")


def _load_tasks() -> list[dict]:
    if not TASKS_FILE.exists():
        return []

    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

        if not content:
            return []

        return json.loads(content)


def _save_tasks(tasks: list[dict]) -> None:
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            tasks,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None
) -> list[dict]:
    """
    Get tasks with optional filters.
    """

    tasks = _load_tasks()

    if status:
        tasks = [
            t for t in tasks
            if t["status"] == status
        ]

    if task_type:
        tasks = [
            t for t in tasks
            if t["task_type"] == task_type
        ]

    return tasks


def add_task(
    title: str,
    description: str,
    task_type: str,
    start_date: str,
    end_date: str,
    status: str = "חדש"
) -> dict:
    """
    Add a new task.
    """

    tasks = _load_tasks()

    next_id = (
        1
        if not tasks
        else max(t["id"] for t in tasks) + 1
    )

    task = Task(
        id=next_id,
        title=title,
        description=description,
        task_type=task_type,
        start_date=start_date,
        end_date=end_date,
        status=status
    )

    tasks.append(task.to_dict())

    _save_tasks(tasks)

    return task.to_dict()


def update_task(
    id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    task_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None
) -> Optional[dict]:
    """
    Update an existing task.
    """

    tasks = _load_tasks()

    for task in tasks:

        if task["id"] == id:

            updates = {
                "title": title,
                "description": description,
                "task_type": task_type,
                "start_date": start_date,
                "end_date": end_date,
                "status": status
            }

            task.update(
                {
                    key: value
                    for key, value in updates.items()
                    if value is not None
                }
            )

            _save_tasks(tasks)

            return task

    return None


def delete_task(id: int) -> dict:
    """
    Delete a task by id.
    """

    tasks = _load_tasks()

    new_tasks = [
        t for t in tasks
        if t["id"] != id
    ]

    if len(new_tasks) == len(tasks):
        return {
            "success": False,
            "message": "Task not found"
        }

    _save_tasks(new_tasks)

    return {
        "success": True,
        "message": "Task deleted successfully"
    }