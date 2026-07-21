"""The FastAPI application: REST endpoints + static web client.

Endpoints
    GET    /api/health
    
    Sources
        GET    /api/sources              list
        POST   /api/sources              add (paste text)
        POST   /api/sources/upload       add (file upload)
        GET    /api/sources/{id}         view full content
        PATCH  /api/sources/{id}         toggle active
        DELETE /api/sources/{id}         remove
    Chat
        POST   /api/chat                 grounded chat (engine + impl A/B)
    Studio
        GET    /api/studio/artifacts     artifact kinds
        POST   /api/studio/generate      generate (501 until stage 3)
    Notes
        GET    /api/notes
        POST   /api/notes
        DELETE /api/notes/{id}

The web client (``client/``) is served as static files at ``/``.
"""
from __future__ import annotations

from langgraph.types import Command

from netfree_unstrict_ssl import unstrict_ssl
unstrict_ssl()

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.staticfiles import StaticFiles

from api import services
from api.schemas import (
    AddNoteRequest,
    AddSourceRequest,
    ApprovalRequest,
    ArtifactKind,
    ChatRequest,
    ChatResponse,
    Note,
    SetActiveRequest,
    SourceDetail,
    SourceInfo,
)

app = FastAPI(title="NotebookLM (LangChain learning project)")


@app.middleware("http")
async def no_store(request: Request, call_next):
    """Disable client caching so edits to the web client show up on a normal reload.

    StaticFiles otherwise lets the browser treat assets as "fresh" without revalidating,
    which makes CSS/JS changes appear not to take effect. Fine for this dev/learning app.
    """
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
@app.post("/api/chat/approve")
def approve(req: ApprovalRequest):

    try:
        print(f"🔄 Resuming with decision: {req.decision}, thread: {req.thread_id}")
        if req.selected_urls:
            print(f"   Selected URLs: {req.selected_urls}")
        
        # Create resume value with proper structure for the middleware
        # The middleware expects: {"decisions": [{"type": "approve"|"reject", ...}]}
        resume_value = {
            "decisions": [
                {
                    "type": req.decision,
                    "selected_urls": req.selected_urls or []
                }
            ]
        }
        
        result = services.chat.agent.invoke(
            Command(
                resume=resume_value
            ),
            config={
                "configurable":{
                    "thread_id": req.thread_id
                }
            }
        )

        print(f"✅ Resume succeeded")
        
        # Extract the final answer
        answer = "No response"
        
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            last_msg = result["messages"][-1]
            
            # If it's an AIMessage object
            if hasattr(last_msg, 'content'):
                content = last_msg.content
                # Handle case where content is a list of content blocks (Anthropic format)
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    answer = ''.join(text_parts)
                else:
                    answer = str(content)
            # If it's a dict with content
            elif isinstance(last_msg, dict) and "content" in last_msg:
                content = last_msg["content"]
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    answer = ''.join(text_parts)
                else:
                    answer = str(content)
        
        print(f"✅ Final answer extracted: {str(answer)[:100]}...")
        
        return {
            "answer": answer
        }
    
    except Exception as e:
        print(f"❌ Error in approve: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


# -- sources -------------------------------------------------------------------


@app.get("/api/sources", response_model=list[SourceInfo])
def get_sources() -> list[SourceInfo]:
    return services.list_sources()


@app.post("/api/sources", response_model=SourceInfo)
def add_source(req: AddSourceRequest) -> SourceInfo:
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Source content is empty.")
    return services.add_source(req.name, req.content)


@app.post("/api/sources/upload", response_model=SourceInfo)
async def upload_source(file: UploadFile = File(...)) -> SourceInfo:
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return services.add_source(file.filename, content)


@app.get("/api/sources/{source_id}", response_model=SourceDetail)
def view_source(source_id: str) -> SourceDetail:
    source = services.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return source


@app.patch("/api/sources/{source_id}", response_model=SourceInfo)
def toggle_source(source_id: str, req: SetActiveRequest) -> SourceInfo:
    source = services.set_source_active(source_id, req.active)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return source


@app.delete("/api/sources/{source_id}")
def delete_source(source_id: str) -> dict[str, bool]:
    if not services.remove_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found.")
    return {"ok": True}


# -- chat ----------------------------------------------------------------------


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return services.run_chat(req)


# -- studio --------------------------------------------------------------------


@app.get("/api/studio/artifacts", response_model=list[ArtifactKind])
def studio_artifacts() -> list[ArtifactKind]:
    return services.list_artifacts()


@app.post("/api/studio/generate", response_model=Note)
def studio_generate(req: dict) -> Note:
    try:
        return services.generate_artifact(req.get("kind", ""), req.get("impl", "A"))
    except services.ComingSoon as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


# -- notes ---------------------------------------------------------------------


@app.get("/api/notes", response_model=list[Note])
def get_notes() -> list[Note]:
    return services.list_notes()


@app.post("/api/notes", response_model=Note)
def add_note(req: AddNoteRequest) -> Note:
    return services.add_note(req.title, req.content)


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: str) -> dict[str, bool]:
    if not services.remove_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found.")
    return {"ok": True}


# Serve the web client. Mounted last so it only catches non-/api paths.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CLIENT_DIR = PROJECT_ROOT / "client"
if _CLIENT_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_CLIENT_DIR), html=True), name="client")
