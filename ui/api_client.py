"""Small, typed boundary between the Streamlit UI and the FastAPI service."""

from __future__ import annotations

import os
from dataclasses import dataclass
import json
from typing import Any, Iterator

import httpx


DEFAULT_API_URL = "https://research-flow-1yal.onrender.com"


class ResearchFlowAPIError(RuntimeError):
    """A user-friendly error returned while communicating with the API."""


@dataclass(frozen=True)
class DraftResponse:
    thread_id: str
    mode: str
    draft: str
    sources: list[dict[str, str]]


@dataclass(frozen=True)
class StreamEvent:
    event: str
    data: dict[str, Any]


def get_api_url() -> str:
    """Return the configured service origin without a trailing slash."""
    return os.getenv("RESEARCHFLOW_API_URL", DEFAULT_API_URL).rstrip("/")


def _detail(response: httpx.Response) -> str:
    try:
        payload: Any = response.json()
    except ValueError:
        return response.text or "The server returned an unexpected response."

    if isinstance(payload, dict) and payload.get("detail"):
        return str(payload["detail"])
    return "The writing service could not complete this request."


def parse_sources(value: Any) -> list[dict[str, str]]:
    """Accept only source records from the API; never manufacture citations."""
    if not isinstance(value, list):
        return []
    return [
        {str(key): str(item_value) for key, item_value in item.items()}
        for item in value
        if isinstance(item, dict) and str(item.get("url", "")).strip()
    ]


def _request(path: str, payload: dict[str, str]) -> DraftResponse:
    try:
        with httpx.Client(timeout=httpx.Timeout(180.0, connect=8.0)) as client:
            response = client.post(f"{get_api_url()}{path}", json=payload)
    except httpx.RequestError as exc:
        raise ResearchFlowAPIError(
            "Could not reach ResearchFlow. Start the FastAPI server and check the API URL."
        ) from exc

    if response.is_error:
        raise ResearchFlowAPIError(_detail(response))

    try:
        data = response.json()
        return DraftResponse(
            thread_id=str(data["thread_id"]),
            mode=str(data.get("mode", "new")),
            draft=str(data["draft"]),
            sources=parse_sources(data.get("sources", [])),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ResearchFlowAPIError(
            "The writing service returned an invalid draft response."
        ) from exc


def generate_draft(prompt: str) -> DraftResponse:
    """Create a fresh workflow thread. The backend creates its UUID."""
    return _request("/write", {"prompt": prompt})


def stream_draft(prompt: str) -> Iterator[StreamEvent]:
    """Yield parsed SSE events from the genuine backend writer stream."""
    try:
        # Research/planning can be quiet for longer than a normal HTTP read timeout
        # before the Writer begins emitting provider deltas.
        stream_timeout = httpx.Timeout(connect=8.0, read=None, write=180.0, pool=180.0)
        with httpx.Client(timeout=stream_timeout) as client:
            with client.stream("POST", f"{get_api_url()}/write/stream", json={"prompt": prompt}) as response:
                if response.is_error:
                    response.read()
                    raise ResearchFlowAPIError(_detail(response))

                event_name = "message"
                data_lines: list[str] = []
                for line in response.iter_lines():
                    if not line:
                        if data_lines:
                            try:
                                data = json.loads("\n".join(data_lines))
                            except json.JSONDecodeError as exc:
                                raise ResearchFlowAPIError("The writing stream sent invalid data.") from exc
                            if not isinstance(data, dict):
                                raise ResearchFlowAPIError("The writing stream sent an invalid event.")
                            if event_name == "error":
                                raise ResearchFlowAPIError(str(data.get("detail", "The writing stream failed.")))
                            yield StreamEvent(event_name, data)
                        event_name = "message"
                        data_lines = []
                    elif line.startswith("event:"):
                        event_name = line.removeprefix("event:").strip()
                    elif line.startswith("data:"):
                        data_lines.append(line.removeprefix("data:").strip())
    except httpx.RequestError as exc:
        raise ResearchFlowAPIError(
            "The writing stream was interrupted. Your draft was not updated; check the backend and try again."
        ) from exc


def revise_draft(instruction: str, thread_id: str) -> DraftResponse:
    """Revise the persisted draft associated with ``thread_id``."""
    return _request("/revise", {"instruction": instruction, "thread_id": thread_id})


def health_check() -> tuple[bool, str]:
    """Return backend availability without raising into the UI."""
    try:
        with httpx.Client(timeout=httpx.Timeout(3.0, connect=2.0)) as client:
            response = client.get(f"{get_api_url()}/health")
        if response.is_success:
            return True, "Writing service connected"
        return False, "Writing service unavailable"
    except httpx.RequestError:
        return False, "Writing service offline"
