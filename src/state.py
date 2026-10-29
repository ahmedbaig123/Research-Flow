
from typing import TypedDict


class ResearchState(TypedDict, total=False):
    # User input
    user_input: str

    # Understanding and planning
    requirements: dict
    plan: dict
    outline: list[str]

    # Research
    research_notes: list[str]
    sources: list[dict[str, str]]

    # Generated content
    draft: str

    # Conversation routing
    conversation_mode: str
    force_revision: bool
    previous_draft: str

    # Optional fields for future features
    feedback: str
    revision_count: int
    critic_approved: bool
    user_approved: bool
