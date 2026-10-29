
from collections.abc import Callable, Iterator
import json
from queue import Queue
from threading import Thread
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from graph.workflow import writing_graph
from agents.writer import stream_writer_chunks


app = FastAPI(
    title="ResearchFlow AI",
    description="An AI writing agent powered by LangGraph.",
    version="1.0.0",
)


class WriteRequest(BaseModel):
    prompt: str = Field(min_length=1, description="What you want to write")
    thread_id: str | None = Field(
        default=None,
        description="Reuse this ID to continue an existing conversation",
    )


class ReviseRequest(BaseModel):
    instruction: str = Field(
        min_length=1,
        description="How to revise the existing draft",
    )
    thread_id: str = Field(
        min_length=1,
        description="ID of the conversation containing the draft",
    )


def run_workflow(
    user_input: str,
    thread_id: str,
    *,
    force_revision: bool = False,
) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    workflow_input: dict[str, str | bool] = {"user_input": user_input}
    if force_revision:
        workflow_input["force_revision"] = True

    try:
        result = writing_graph.invoke(
            workflow_input,
            config=config,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The writing workflow failed. Check the backend terminal logs.",
        ) from exc

    return {
        "thread_id": thread_id,
        "mode": result.get("conversation_mode", "new"),
        "draft": result.get("draft", ""),
    }


def run_workflow_stream(
    user_input: str,
    thread_id: str,
    on_chunk: Callable[[str], None],
) -> dict:
    """Run the existing graph while forwarding genuine writer token deltas.

    The graph remains responsible for persisting the final node return value. The
    callback is a ContextVar in ``agents.writer``, so it never enters checkpointed
    state or changes the regular /write workflow.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        with stream_writer_chunks(on_chunk):
            result = writing_graph.invoke({"user_input": user_input}, config=config)
    except Exception as exc:
        raise RuntimeError("The writing workflow failed. Check the backend terminal logs.") from exc

    return {
        "thread_id": thread_id,
        "mode": result.get("conversation_mode", "new"),
        "draft": result.get("draft", ""),
    }


def sse_event(event: str, data: dict) -> str:
    """Serialize one Server-Sent Event without allowing multiline framing."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/health")
def health_check():
    return {"status": "healthy", "app": "ResearchFlow AI"}


@app.post("/write")
def write(request: WriteRequest):
    thread_id = request.thread_id or str(uuid4())

    return run_workflow(
        user_input=request.prompt,
        thread_id=thread_id,
    )


@app.post("/write/stream")
def write_stream(request: WriteRequest):
    """Create a draft and stream actual Groq writer deltas as SSE events.

    Event sequence: ``start`` (thread ID), zero or more ``chunk`` events, and a
    terminal ``complete`` event containing the persisted final draft. Failures are
    sent as a terminal ``error`` event because headers were already streamed.
    """
    thread_id = request.thread_id or str(uuid4())
    events: Queue[tuple[str, dict] | None] = Queue()

    def invoke_graph() -> None:
        try:
            result = run_workflow_stream(
                request.prompt,
                thread_id,
                lambda text: events.put(("chunk", {"text": text})),
            )
            events.put(("complete", result))
        except Exception:
            events.put(
                (
                    "error",
                    {"detail": "The writing workflow failed. Check the backend terminal logs."},
                )
            )
        finally:
            events.put(None)

    def event_stream() -> Iterator[str]:
        yield sse_event("start", {"thread_id": thread_id})
        worker = Thread(target=invoke_graph, name=f"researchflow-stream-{thread_id}", daemon=True)
        worker.start()
        while event := events.get():
            event_name, data = event
            yield sse_event(event_name, data)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/revise")
def revise(request: ReviseRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        state = writing_graph.get_state(config)

        if not state.values or not state.values.get("draft"):
            raise HTTPException(
                status_code=404,
                detail="No existing draft found for this thread_id.",
            )

        result = run_workflow(
            user_input=request.instruction,
            thread_id=request.thread_id,
            force_revision=True,
        )

        if result["mode"] != "revise":
            raise HTTPException(
                status_code=400,
                detail="The workflow classified this request as a new writing task.",
            )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not revise the draft. Check the backend terminal logs.",
        ) from exc
