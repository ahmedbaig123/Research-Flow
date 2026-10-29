"""Focused tests for real writer streaming and the SSE endpoint.

These use fakes only; they never make a Groq, Tavily, or network request.
"""

from types import SimpleNamespace

from fastapi.testclient import TestClient

import api
from agents import writer
from src.models import WritingRequirements, writingplan


def test_writer_forwards_real_provider_deltas(monkeypatch):
    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="A streamed "))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="draft."))]),
    ]

    class Completions:
        def create(self, **kwargs):
            assert kwargs["stream"] is True
            return iter(chunks)

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    monkeypatch.setattr(writer, "client", fake_client)
    received: list[str] = []

    with writer.stream_writer_chunks(received.append):
        draft = writer.write_draft(
            WritingRequirements(topic="Streaming", writing_type="article"),
            writingplan(document_type="article", purpose="test", structure=[], writing_instructions="test"),
            [],
        )

    assert draft == "A streamed draft."
    assert received == ["A streamed ", "draft."]


def test_stream_endpoint_emits_complete_persisted_draft(monkeypatch):
    def fake_workflow(prompt, thread_id, on_chunk):
        on_chunk("Saved ")
        on_chunk("draft")
        # The real function returns only after writing_graph.invoke has checkpointed.
        return {
            "thread_id": thread_id,
            "mode": "new",
            "draft": "Saved draft",
            "sources": [{"title": "Example source", "url": "https://example.com"}],
        }

    monkeypatch.setattr(api, "run_workflow_stream", fake_workflow)
    with TestClient(api.app) as client:
        response = client.post("/write/stream", json={"prompt": "Write something"})

    assert response.status_code == 200
    assert "event: start" in response.text
    assert 'event: chunk\ndata: {"text": "Saved "}' in response.text
    assert 'event: complete' in response.text
    assert '"draft": "Saved draft"' in response.text
    assert '"url": "https://example.com"' in response.text


def test_streamed_draft_is_available_to_the_existing_revision_endpoint(monkeypatch):
    class CheckpointGraph:
        def __init__(self):
            self.values: dict[str, dict] = {}
            self.last_thread_id = ""

        def invoke(self, payload, config):
            thread_id = config["configurable"]["thread_id"]
            self.last_thread_id = thread_id
            if payload["user_input"] == "Initial prompt":
                # This is the same callback consumed by writer_node in production.
                writer._chunk_callback.get()("Persistent draft")
                result = {"conversation_mode": "new", "draft": "Persistent draft"}
            else:
                result = {"conversation_mode": "revise", "draft": "Revised persistent draft"}
            self.values[thread_id] = result
            return result

        def get_state(self, config):
            return SimpleNamespace(values=self.values.get(config["configurable"]["thread_id"], {}))

    graph = CheckpointGraph()
    monkeypatch.setattr(api, "writing_graph", graph)

    with TestClient(api.app) as client:
        stream_response = client.post("/write/stream", json={"prompt": "Initial prompt"})
        revision_response = client.post(
            "/revise",
            json={"thread_id": graph.last_thread_id, "instruction": "Make it shorter"},
        )

    assert '"draft": "Persistent draft"' in stream_response.text
    assert revision_response.status_code == 200
    assert revision_response.json()["draft"] == "Revised persistent draft"
