# ResearchFlow AI

ResearchFlow AI is a LangGraph-powered writing agent with a FastAPI service and a Streamlit writing workspace.

## Run locally

Use two terminals from the project directory.

```powershell
uv run uvicorn api:app --reload
```

```powershell
uv run streamlit run app.py
```

The Streamlit app communicates only with the FastAPI service. It reads the service origin from `RESEARCHFLOW_API_URL` and defaults to `http://127.0.0.1:8000`.

Draft generation uses `POST /write/stream`, a Server-Sent Events endpoint. It forwards actual Groq token deltas as the Writer node produces them, then emits a final `complete` event only after the same LangGraph invocation has saved its final draft to SQLite. The existing non-streaming `/write` and `/revise` endpoints remain available.

## Verify streaming behavior

```powershell
uv run python -m pytest tests/test_streaming.py -q
```

These isolated tests fake the provider response: they verify token forwarding, SSE framing, and streamed-draft continuity into the existing revision endpoint without consuming Groq or Tavily API calls.

## Workspace behavior

- Generate creates a fresh backend thread; the returned `thread_id` is retained in Streamlit session state and used for revisions.
- **New document** clears the active thread and draft so it cannot accidentally revise the previous document.
- The sidebar keeps documents created in the current browser session. There is no endpoint to enumerate saved backend threads, so it does not claim to show persistent history.
- Markdown download and a direct Copy draft control are available in the draft toolbar.

## Current API limitations

`POST /write`, `POST /write/stream`, and `POST /revise` return the graph's real `sources` records when research finds them, and the workspace displays those records as links. Persistent cross-session history still needs a dedicated backend endpoint that lists available thread metadata.
