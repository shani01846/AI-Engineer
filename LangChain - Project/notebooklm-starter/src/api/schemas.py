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


class ApprovalAction(BaseModel):
    """Action that requires approval."""

    name: str

    args: dict


class ApprovalData(BaseModel):
    """
    Data shown to the user before approval.
    """

    status: ApprovalStatus = "none"

    actions: list[ApprovalAction] = Field(
        default_factory=list
    )

    urls: list[str] = Field(
        default_factory=list
    )
    
    # Type of approval: "source_selection" for request_source_approval, 
    # "scrape_confirmation" for scrape_source/crawl_source
    approval_type: Literal["source_selection", "scrape_confirmation"] = "scrape_confirmation"


class ApprovalRequest(BaseModel):
    """
    User decision after HITL interrupt.
    """

    thread_id: str

    decision: Literal[
        "approve",
        "reject",
    ]
    
    # Selected URLs (for request_source_approval)
    selected_urls: list[str] | None = None





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

    tools_used: list[str] = Field(
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