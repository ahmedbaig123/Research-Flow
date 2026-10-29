"""Regression coverage for explicit revisions that do not match keyword rules."""

from types import SimpleNamespace

import api
from graph.workflow import classify_node


def test_explicit_revision_skips_classifier(monkeypatch):
    def unexpected_classifier(*args, **kwargs):
        raise AssertionError("The classifier must not run for /revise requests")

    monkeypatch.setattr("graph.workflow.classify_request", unexpected_classifier)
    result = classify_node(
        {"force_revision": True, "user_input": "Keep it under three stanzas", "draft": "Old draft"}
    )
    assert result == {"conversation_mode": "revise", "force_revision": False}


def test_revise_endpoint_forces_revision_route(monkeypatch):
    captured: dict = {}

    class Graph:
        def get_state(self, config):
            return SimpleNamespace(values={"draft": "Existing draft"})

        def invoke(self, workflow_input, config):
            captured.update(workflow_input)
            return {"conversation_mode": "revise", "draft": "Three stanzas"}

    monkeypatch.setattr(api, "writing_graph", Graph())
    response = api.revise(api.ReviseRequest(thread_id="thread-1", instruction="Keep it under three stanzas"))

    assert captured["force_revision"] is True
    assert response["draft"] == "Three stanzas"
