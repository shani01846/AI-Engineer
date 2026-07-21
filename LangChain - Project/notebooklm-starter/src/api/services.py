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
import datetime


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

    # Ensure result.text is a string
    answer_text = result.text
    if isinstance(answer_text, list):
        # Handle list of content blocks
        text_parts = []
        for block in answer_text:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
            else:
                text_parts.append(str(block))
        answer_text = ''.join(text_parts)
    else:
        answer_text = str(answer_text) if answer_text else "No response"

    response = ChatResponse(

        answer=answer_text,

        citations=citations,

        engine="gemini",

        thread_id=thread_id,

        interrupt=result.interrupt,

    )

    # If interrupted, create approval data
    if result.interrupt:
        from api.schemas import ApprovalData, ApprovalAction
        
        actions = []
        urls = result.approval_urls or []
        
        # Determine approval type based on tool name
        approval_type = "scrape_confirmation"
        if result.tool_name == "request_source_approval":
            approval_type = "source_selection"
        
        for url in urls:
            actions.append(
                ApprovalAction(
                    name=result.tool_name or "scurce",
                    args={"url": url}
                )
            )
        
        response.approval = ApprovalData(
            status="waiting",
            actions=actions,
            urls=urls,
            approval_type=approval_type
        )

    return response






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
        key="summary",
        title="Summary",
        icon="📄",
        status="ready",
    ),
    ArtifactKind(
        key="powerpoint",
        title="PowerPoint",
        icon="📑",
        status="ready",
    ),
    ArtifactKind(
        key="faq",
        title="FAQ",
        icon="❓",
        status="ready",
    ),
    ArtifactKind(
        key="quiz",
        title="Quiz",
        icon="🧠",
        status="ready",
    ),
    ArtifactKind(
        key="infographic",
        title="Infographic",
        icon="📊",
        status="ready",
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
    """Generate an artifact based on active sources."""
    
    artifact = _ARTIFACTS_BY_KEY.get(kind)
    title = artifact.title if artifact else "Artifact"
    
    try:
        # Get all active sources
        active_sources = store.list()
        active_sources = [s for s in active_sources if s.active]
        
        if not active_sources:
            raise ComingSoon(
                f"Please add sources first to generate a {title}."
            )
        
        # Combine all source content
        combined_content = "\n\n---\n\n".join(
            f"## {s.name}\n{s.content}"
            for s in active_sources
        )
        
        # Use the chat model to generate the artifact
        try:
            from agents.chat import MODEL
            from langchain_core.messages import HumanMessage
        except Exception as e:
            raise ComingSoon(f"Failed to load model: {str(e)}")
        
        prompts = {
            "summary": f"""Based on the following sources, write a comprehensive executive summary (500-800 words):

{combined_content}

Provide a well-structured summary with clear headings.""",
            
            "powerpoint": f"""Based on the following sources, create presentation slide content with 6-8 slides. 
For each slide, provide:
- SLIDE TITLE
- Bullet points (3-5 per slide)

{combined_content}

Create engaging, clear slide content suitable for a PowerPoint presentation.""",
            
            "faq": f"""Based on the following sources, create a FAQ (Frequently Asked Questions) document with 8-10 questions.
Format each Q&A as:
Q: [Question]
A: [Answer]

{combined_content}

Ensure questions are practical and answers are clear and concise.""",
            
            "quiz": f"""Based on the following sources, create a quiz with 10 multiple-choice questions.
Format each question as:
Q#: [Question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Answer: [Correct option letter]

{combined_content}

Create questions that test understanding of the key concepts.""",
            
            "infographic": f"""Based on the following sources, create a text-based infographic outline.
Include:
- Key statistics
- Visual ASCII representation suggestions
- Important points
- Data relationships

{combined_content}

Present information in a structured, visually organized way.""",
        }
        
        prompt = prompts.get(kind, prompts["summary"])
        
        response = MODEL.invoke([
            HumanMessage(content=prompt)
        ])
        
        content = response.content
        if isinstance(content, list):
            # Handle Gemini's content blocks format
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = ''.join(text_parts)
        
        note = Note(
            id=uuid.uuid4().hex[:8],
            title=f"{title} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            content=str(content)
        )
        
        _NOTES[note.id] = note
        return note
        
    except ComingSoon:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in generate_artifact: {error_details}")
        raise ComingSoon(
            f"Error generating {title}: {str(e)}"
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