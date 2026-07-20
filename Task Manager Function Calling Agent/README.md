# Task Manager Function Calling Agent

An AI-powered task management app with a React client and a FastAPI server.

The assistant receives natural language requests and uses function calling to create, update, delete, and retrieve tasks.

## Project Structure

- `Client/task-chat-client`: React + TypeScript + Vite frontend
- `Server`: FastAPI backend and AI agent logic
- `assets/example CHAT.png`: app screenshot

## Features

- Chat-based task management
- Function-calling agent for task operations
- Live task list shown in the UI
- Task persistence with `Server/tasks.json`

## Tech Stack

- Frontend: React, TypeScript, Vite, Axios
- Backend: FastAPI, Python
- AI: Google GenAI (`gemini-flash-latest`)

## Prerequisites

- Node.js (recommended LTS)
- Python 3.10+
- A valid Gemini API key

## Setup

### 1) Server

From `Server`:

```bash
pip install fastapi uvicorn python-dotenv google-genai
```

Create or update `Server/.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Run the backend:

```bash
uvicorn main:app --reload
```

The server is expected at `http://localhost:8000`.

### 2) Client

From `Client/task-chat-client`:

```bash
npm install
npm run dev
```

The client is expected at `http://localhost:5173`.

## API Endpoints

- `GET /` health message
- `GET /tasks` fetch all tasks
- `POST /chat` send user prompt to the AI agent

## Screenshot

![Task Agent Running Example](assets/example%20CHAT.png)

## Notes

- If chat requests fail, verify that both server and client are running.
- If AI responses fail, verify `GEMINI_API_KEY` in `Server/.env`.
