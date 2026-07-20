tools = [
    {
        "name": "add_task",
        "description": "Adds a new task.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Task description"
                },
                "task_type": {
                    "type": "string",
                    "description": "Task category"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD"
                },
                "status": {
                    "type": "string",
                    "description": "Task status"
                }
            },
            "required": [
                "title",
                "description",
                "task_type",
                "start_date",
                "end_date",
                "status"
            ]
        }
    },

    {
        "name": "get_tasks",
        "description": "Returns tasks according to optional filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string"
                },
                "task_type": {
                    "type": "string"
                }
            }
        }
    },

    {
        "name": "update_task",
        "description": "Updates an existing task.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer"
                },
                "title": {
                    "type": "string"
                },
                "description": {
                    "type": "string"
                },
                "task_type": {
                    "type": "string"
                },
                "start_date": {
                    "type": "string"
                },
                "end_date": {
                    "type": "string"
                },
                "status": {
                    "type": "string"
                }
            },
            "required": [
                "id"
            ]
        }
    },

    {
        "name": "delete_task",
        "description": "Deletes a task.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer"
                }
            },
            "required": [
                "id"
            ]
        }
    }
]