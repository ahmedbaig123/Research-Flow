from pydantic import BaseModel, Field


class WritingRequirements(BaseModel):
    topic: str = Field(description="What the user wants to write about")

    writing_type: str = Field(
        description="The requested format, such as blog, essay, recipe, poem, review, report, or story"
    )


    target_length: int | None = None
    audience: str | None = None
    tone: str | None = None

    research_required: bool = False
    citation_style: str | None = None

    clarification_needed: bool = False
    clarification_question: str | None = None

class writingplan(BaseModel):
    document_type:str
    purpose: str

    structure: list[str] = Field(
        description=(
             "Ordered sections, steps, verses, or content blocks. "
            "Use a structure suited to the requested writing type."
        )
    )

    writing_instructions: str
    research_questions: list[str] = Field(default_factory=list)
    needs_research: bool = False
    citation_requirements: str | None = None

class CriticFeedback(BaseModel):
    approved: bool = Field(
        description="Whether the draft meets the review criteria"
    )
    overall_feedback: str
    issues: list[str] = Field(default_factory=list)
    revision_instructions: str=""