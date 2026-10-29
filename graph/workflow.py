
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END

from src.state import ResearchState
from src.models import WritingRequirements, writingplan

from agents.understanding import understand_request
from agents.planner import create_plan
from agents.researcher import research_topic
from agents.writer import write_draft
from agents.followup import classify_request
from agents.revise_draft import revise_draft


def classify_node(state: ResearchState):
    # /revise has already verified that this thread owns a draft. Do not make a
    # second LLM classification call for an explicit revision instruction.
    if state.get("force_revision"):
        return {"conversation_mode": "revise", "force_revision": False}

    mode = classify_request(
        user_input=state["user_input"],
        previous_draft=state.get("draft"),
    )

    print("CLASSIFIED MODE:", mode)

    return {"conversation_mode": mode}


def route_request(state: ResearchState):
    return state["conversation_mode"]


def understanding_node(state: ResearchState):
    requirements = understand_request(state["user_input"])

    return {
        "requirements": requirements.model_dump()
    }


def planner_node(state: ResearchState):
    requirements = WritingRequirements.model_validate(
        state["requirements"]
    )

    plan = create_plan(requirements)

    return {
        "plan": plan.model_dump(),
        "outline": plan.structure,
    }


def researcher_node(state: ResearchState):
    requirements = WritingRequirements.model_validate(
        state["requirements"]
    )

    plan = writingplan.model_validate(state["plan"])

    return research_topic(requirements, plan)


def writer_node(state: ResearchState):
    requirements = WritingRequirements.model_validate(
        state["requirements"]
    )

    plan = writingplan.model_validate(state["plan"])

    draft = write_draft(
        requirements=requirements,
        plan=plan,
        research_notes=state.get("research_notes", []),
    )

    return {"draft": draft}


def revision_node(state: ResearchState):
    draft = revise_draft(
        previous_draft=state["draft"],
        user_request=state["user_input"],
    )

    return {"draft": draft}


builder = StateGraph(ResearchState)

builder.add_node("classify", classify_node)
builder.add_node("understanding", understanding_node)
builder.add_node("planner", planner_node)
builder.add_node("researcher", researcher_node)
builder.add_node("writer", writer_node)
builder.add_node("revision", revision_node)

builder.add_edge(START, "classify")

builder.add_conditional_edges(
    "classify",
    route_request,
    {
        "new": "understanding",
        "revise": "revision",
    },
)

builder.add_edge("understanding", "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")

builder.add_edge("writer", END)
builder.add_edge("revision", END)

connection = sqlite3.connect(
    "researchflow_checkpoints.sqlite",
    check_same_thread=False,
)

checkpointer = SqliteSaver(connection)

writing_graph = builder.compile(checkpointer=checkpointer)
