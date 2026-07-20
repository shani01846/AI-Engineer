"""
Backend services: translate API requests into the LangChain code.

This is the thin layer between the API contract and the LangChain implementation.

Supports:
- Source management
- Notes
- RAG chat
- Human-In-The-Loop resume flow
"""

from __future__ import annotations


import uuid


from langgraph.types import Command


from api.schemas import (
    ArtifactKind,
    ChatRequest,
    ChatResponse,
    Citation,
    Note,
    SourceDetail,
    SourceInfo,
)


from agents import chat

from core.store import store




class ComingSoon(Exception):
    """Raised for capabilities not implemented yet."""
    pass




# ------------------------------------------------------------------------------
# SOURCES
# ------------------------------------------------------------------------------


def _to_info(source) -> SourceInfo:

    return SourceInfo(
        id=source.id,
        name=source.name,
        chars=len(source.content),
        active=source.active,
    )




def list_sources() -> list[SourceInfo]:

    return [
        _to_info(s)
        for s in store.list()
    ]




def get_source(
    source_id: str
) -> SourceDetail | None:


    source = store.get(
        source_id
    )


    if source is None:
        return None


    return SourceDetail(

        id=source.id,

        name=source.name,

        chars=len(source.content),

        active=source.active,

        content=source.content,
    )





def add_source(
    name: str | None,
    content: str
) -> SourceInfo:


    name = (
        (name or "").strip()
        or _auto_name(content)
    )


    return _to_info(

        store.add(

            name=name,

            content=content,
        )
    )





def set_source_active(
    source_id: str,
    active: bool
) -> SourceInfo | None:


    source = store.set_active(
        source_id,
        active
    )


    return (
        _to_info(source)
        if source
        else None
    )





def remove_source(
    source_id: str
) -> bool:

    return store.remove(
        source_id
    )





def _auto_name(
    content: str
) -> str:


    first_line = (

        content.strip().splitlines()[0]

        if content.strip()

        else "Pasted source"
    )


    first_line = (
        first_line
        .lstrip("# ")
        .strip()
    )


    return (
        first_line[:40]
        or "Pasted source"
    ) + ".txt"







# ------------------------------------------------------------------------------
# CHAT
# ------------------------------------------------------------------------------


def run_chat(
    req: ChatRequest
) -> ChatResponse:


    thread_id = (
        req.thread_id
        or uuid.uuid4().hex
    )


    result = chat.answer(

        question=req.message,

        thread_id=thread_id,

    )



    citations = [

        Citation(
            source=name
        )

        for name in result.sources
    ]




    return ChatResponse(

        answer=result.text,

        citations=citations,

        engine="gemini",

        thread_id=thread_id,

    )






# ------------------------------------------------------------------------------
# HUMAN IN THE LOOP RESUME
# ------------------------------------------------------------------------------


def resume_chat(
    thread_id: str,
    decision: str
):


    """
    Continue interrupted LangGraph execution.

    Called after user approves/rejects
    scrape_source or crawl_source.
    """



    if decision not in [
        "approve",
        "reject"
    ]:

        raise ValueError(
            "Invalid approval decision"
        )




    result = chat.agent.invoke(

        Command(

            resume={

                "decisions":[

                    {

                        "type":
                        decision

                    }

                ]

            }

        ),


        config={

            "configurable":{

                "thread_id":
                thread_id

            }

        }

    )


    return result







# ------------------------------------------------------------------------------
# STUDIO
# ------------------------------------------------------------------------------


ARTIFACTS = [

    ArtifactKind(

        key="infographic",

        title="Infographic",

        icon="📊",

        status="planned",
    ),


    ArtifactKind(

        key="powerpoint",

        title="PowerPoint",

        icon="📑",

        status="planned",
    ),


    ArtifactKind(

        key="summary",

        title="Summary",

        icon="📄",

        status="planned",
    ),


    ArtifactKind(

        key="faq",

        title="FAQ",

        icon="❓",

        status="planned",
    ),

]



_ARTIFACTS_BY_KEY = {

    a.key:a

    for a in ARTIFACTS

}





def list_artifacts():

    return ARTIFACTS





def generate_artifact(
    kind: str,
    impl: str
) -> Note:


    artifact = (
        _ARTIFACTS_BY_KEY.get(kind)
    )


    title = (

        artifact.title

        if artifact

        else "Artifact"

    )


    raise ComingSoon(

        f"{title} generation is coming soon."

    )






# ------------------------------------------------------------------------------
# NOTES
# ------------------------------------------------------------------------------


_NOTES: dict[str, Note] = {}




def list_notes():

    return list(
        _NOTES.values()
    )





def add_note(
    title: str,
    content: str
):


    note = Note(

        id=uuid.uuid4().hex[:8],

        title=(
            title.strip()
            or "Untitled note"
        ),

        content=content,

    )


    _NOTES[note.id] = note


    return note





def remove_note(
    note_id: str
):

    return (
        _NOTES.pop(
            note_id,
            None
        )
        is not None
    )