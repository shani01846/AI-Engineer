"""
The API contract shared between backend and client.

These Pydantic models are the stable boundary between backend and frontend.

Supports:
- Sources management
- Grounded chat
- Human-In-The-Loop approval flow
- Studio artifacts
- Notes
"""


from __future__ import annotations


from typing import Literal

from pydantic import BaseModel, Field



Impl = Literal["A", "B"]



# ============================================================================
# Sources
# ============================================================================


class SourceInfo(BaseModel):
    """
    A document in the notebook list.
    Does not include content.
    """

    id: str
    name: str
    chars: int
    active: bool



class SourceDetail(SourceInfo):
    """
    A source with full content.
    """

    content: str



class AddSourceRequest(BaseModel):
    """
    Add source by text.
    """

    name: str | None = None

    content: str



class SetActiveRequest(BaseModel):

    active: bool





# ============================================================================
# Chat
# ============================================================================


class Citation(BaseModel):
    """
    Source used for grounding the answer.
    """

    source: str

    snippet: str | None = None




class ChatRequest(BaseModel):
    """
    Normal chat request.
    """

    message: str

    # LangGraph checkpoint thread
    thread_id: str | None = None





# ============================================================================
# Human In The Loop
# ============================================================================


ApprovalStatus = Literal[
    "none",
    "waiting",
    "approved",
    "rejected",
]


ApprovalAction = Literal[
    "scrape_source",
    "crawl_source",
]


class ApprovalAction(BaseModel):

    name: str

    args: dict


class ApprovalData(BaseModel):

    status: str

    actions: list[ApprovalAction] = Field(
        default_factory=list
    )
class ApprovalRequest(BaseModel):
    """
    User decision after HITL interrupt.
    """

    thread_id: str


    decision: Literal[
        "approve",
        "reject",
    ]





class ApprovalData(BaseModel):
    """
    Data shown to the user before approval.
    """

    status: ApprovalStatus = "none"


    tool: ApprovalAction | None = None


    message: str | None = None


    urls: list[str] = Field(
        default_factory=list
    )





# ============================================================================
# Chat Response
# ============================================================================


class ChatResponse(BaseModel):
    """
    Chat response.

    Can represent:
    - Normal answer
    - Waiting for human approval
    """

    answer: str


    citations: list[Citation] = Field(
        default_factory=list
    )


    engine: str = "chat"



    # True when LangGraph interrupted
    interrupt: bool = False



    # HITL information
    approval: ApprovalData | None = None



    # Required for resume
    thread_id: str | None = None





# ============================================================================
# Studio
# ============================================================================


class ArtifactKind(BaseModel):
    """
    Artifact shown in Studio panel.
    """

    key: str

    title: str

    icon: str

    status: Literal[
        "ready",
        "planned",
    ]





class GenerateArtifactRequest(BaseModel):

    kind: str

    impl: Impl = "A"





# ============================================================================
# Notes
# ============================================================================


class Note(BaseModel):

    id: str

    title: str

    content: str





class AddNoteRequest(BaseModel):

    title: str

    content: str