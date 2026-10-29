"""ResearchFlow AI — a Streamlit workspace for the existing FastAPI workflow."""

from __future__ import annotations

from html import escape
import json
import re
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

from ui.api_client import (
    ResearchFlowAPIError,
    get_api_url,
    health_check,
    revise_draft,
    parse_sources,
    stream_draft,
)
from ui.styles import apply_styles


st.set_page_config(page_title="ResearchFlow AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
apply_styles()


def setup_state() -> None:
    defaults = {
        "thread_id": None,
        "draft": "",
        "draft_mode": "",
        "sources": [],
        "title": "Untitled document",
        "documents": [],
        "prompt": "",
        "revision": "",
        "clear_revision_on_rerun": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def title_from(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip().rstrip(".")
    return (cleaned[:52] + "…") if len(cleaned) > 53 else (cleaned or "Untitled document")


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def save_active_document() -> None:
    """Upsert the live draft in this browser session's lightweight document list."""
    thread_id = st.session_state.thread_id
    if not thread_id:
        return
    document = {
        "thread_id": thread_id,
        "title": st.session_state.title,
        "draft": st.session_state.draft,
        "mode": st.session_state.draft_mode,
        "sources": st.session_state.sources,
    }
    documents = st.session_state.documents
    st.session_state.documents = [item for item in documents if item["thread_id"] != thread_id]
    st.session_state.documents.insert(0, document)


def begin_new_document() -> None:
    st.session_state.thread_id = None
    st.session_state.draft = ""
    st.session_state.draft_mode = ""
    st.session_state.sources = []
    st.session_state.title = "Untitled document"
    st.session_state.prompt = ""
    st.session_state.revision = ""


def select_document(thread_id: str) -> None:
    selected = next(item for item in st.session_state.documents if item["thread_id"] == thread_id)
    st.session_state.thread_id = selected["thread_id"]
    st.session_state.title = selected["title"]
    st.session_state.draft = selected["draft"]
    st.session_state.draft_mode = selected["mode"]
    st.session_state.sources = selected.get("sources", [])
    st.session_state.revision = ""


@st.cache_data(ttl=12, show_spinner=False)
def service_status(api_url: str) -> tuple[bool, str]:
    # api_url is an explicit cache key, so changing the environment gets a fresh result.
    return health_check()


def sidebar() -> None:
    with st.sidebar:
        st.markdown("<div class='rf-brand'><div class='rf-mark'>R</div><div class='rf-brand-name'>ResearchFlow <span>AI</span></div></div>", unsafe_allow_html=True)
        if st.button("＋  New document", use_container_width=True, type="primary"):
            begin_new_document()
            st.rerun()

        st.markdown("<div class='sidebar-heading'>This session</div>", unsafe_allow_html=True)
        if st.session_state.documents:
            for document in st.session_state.documents:
                current = document["thread_id"] == st.session_state.thread_id
                label = ("● " if current else "") + document["title"]
                if st.button(label, key=f"doc-{document['thread_id']}", use_container_width=True):
                    select_document(document["thread_id"])
                    st.rerun()
        else:
            st.caption("Drafts you create in this browser session will appear here.")

        st.markdown("<div class='sidebar-heading'>Connection</div>", unsafe_allow_html=True)
        online, message = service_status(get_api_url())
        dot_class = "dot" if online else "dot off"
        st.markdown(f"<div class='status'><span class='{dot_class}'></span>{message}</div>", unsafe_allow_html=True)
        st.caption(get_api_url())
        st.markdown("<div class='sidebar-heading'>Preferences</div>", unsafe_allow_html=True)
        st.caption("Your document history is local to this browser session. The current thread is persisted by the backend.")


def generate() -> None:
    prompt = st.session_state.prompt.strip()
    if not prompt:
        st.warning("Describe what you want to write before generating a draft.")
        return
    streamed_draft = ""
    thread_id: str | None = None
    final_draft = ""
    final_mode = "new"
    final_sources: list[dict[str, str]] = []
    with st.status("ResearchFlow is generating your draft…", expanded=True) as status:
        preview = st.empty()
        try:
            for event in stream_draft(prompt):
                if event.event == "start":
                    thread_id = str(event.data["thread_id"])
                elif event.event == "chunk":
                    streamed_draft += str(event.data.get("text", ""))
                    preview.markdown(streamed_draft + "▌")
                elif event.event == "complete":
                    final_draft = str(event.data.get("draft", ""))
                    final_mode = str(event.data.get("mode", "new"))
                    final_sources = parse_sources(event.data.get("sources", []))
                    thread_id = str(event.data.get("thread_id", thread_id or ""))
        except ResearchFlowAPIError as exc:
            status.update(label="Generation interrupted", state="error", expanded=True)
            st.error(str(exc))
            return

        if not thread_id or not final_draft:
            status.update(label="Generation did not return a draft", state="error", expanded=True)
            st.error("The writing stream ended before a complete draft was saved. Please try again.")
            return
        status.update(label="Draft complete", state="complete", expanded=False)

    st.session_state.thread_id = thread_id
    st.session_state.draft = final_draft
    st.session_state.draft_mode = final_mode
    st.session_state.sources = final_sources
    st.session_state.title = title_from(prompt)
    st.session_state.revision = ""
    save_active_document()
    st.success("Draft ready.")
    st.rerun()


def revise() -> None:
    instruction = st.session_state.revision.strip()
    if not instruction:
        st.warning("Add an instruction before requesting a revision.")
        return
    if not st.session_state.thread_id:
        st.error("Create a draft before requesting a revision.")
        return
    # Deliberately do not change the existing draft until the API confirms success.
    with st.spinner("Refining the draft while keeping your current version visible…"):
        try:
            response = revise_draft(instruction, st.session_state.thread_id)
        except ResearchFlowAPIError as exc:
            st.error(str(exc))
            return

    st.session_state.draft = response.draft
    st.session_state.draft_mode = response.mode
    st.session_state.sources = response.sources
    # The revision text area has already been created in this run. Clear it at
    # the beginning of the next rerun, before Streamlit instantiates the widget.
    st.session_state.clear_revision_on_rerun = True
    save_active_document()
    st.success("Revision applied.")
    st.rerun()


def apply_prompt_suggestion(suggestion: str) -> None:
    """Set the composer value during the button callback lifecycle."""
    st.session_state.prompt = suggestion


def composer() -> None:
    with st.container(border=True):
        st.text_area(
            "What should ResearchFlow write?",
            key="prompt",
            placeholder="For example: Write a research-backed article about how edge AI is changing industrial maintenance.",
            height=112,
            label_visibility="collapsed",
        )
        suggestions = [
            "Write a research-backed article.",
            "Create a technical blog post.",
            "Compare two documents.",
            "Draft a professional report.",
        ]
        st.markdown("<div class='suggestion-note'>Try a starting point</div>", unsafe_allow_html=True)
        columns = st.columns(4)
        for column, suggestion in zip(columns, suggestions):
            with column:
                st.button(
                    suggestion,
                    key=f"suggest-{suggestion}",
                    use_container_width=True,
                    on_click=apply_prompt_suggestion,
                    args=(suggestion,),
                )
        _, generate_column = st.columns([3, 1])
        with generate_column:
            if st.button("Generate draft", type="primary", use_container_width=True):
                generate()


def copy_control(text: str) -> None:
    """A self-contained copy button with an older-browser fallback."""
    # Escape HTML-significant characters so a draft cannot close the script tag.
    safe_text = json.dumps(text).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    components.html(
        f"""
        <button id="copy" type="button" aria-label="Copy draft">Copy draft</button>
        <script>
          const text = {safe_text};
          const button = document.getElementById('copy');
          async function copy() {{
            try {{
              if (navigator.clipboard) await navigator.clipboard.writeText(text);
              else {{
                const area = document.createElement('textarea');
                area.value = text; document.body.appendChild(area); area.select();
                document.execCommand('copy'); area.remove();
              }}
              button.textContent = 'Copied';
              setTimeout(() => button.textContent = 'Copy draft', 1600);
            }} catch (error) {{ button.textContent = 'Copy failed'; }}
          }}
          button.addEventListener('click', copy);
        </script>
        <style>
          html,body {{ margin:0; background:transparent; font-family:Arial,sans-serif; }}
          button {{ width:100%; height:35px; border-radius:8px; border:1px solid rgba(185,175,224,.2); background:transparent; color:#d9d5e8; cursor:pointer; font-size:13px; }}
          button:hover {{ border-color:rgba(178,164,244,.48); background:#2a243b; color:white; }}
        </style>
        """,
        height=39,
    )


def draft_workspace() -> None:
    if st.session_state.clear_revision_on_rerun:
        st.session_state.revision = ""
        st.session_state.clear_revision_on_rerun = False

    draft = st.session_state.draft
    mode = st.session_state.draft_mode or "new"
    st.markdown("<div class='eyebrow'>Writing workspace</div>", unsafe_allow_html=True)
    st.markdown(f"<h2 class='workspace-title'>{escape(st.session_state.title)}</h2>", unsafe_allow_html=True)
    st.markdown("<p class='workspace-subtitle'>A focused place to turn a good brief into a considered draft.</p>", unsafe_allow_html=True)

    if not draft:
        st.markdown("<section class='welcome'><div class='eyebrow'>Research, reason, write</div><h1>Give your best ideas a clearer first draft.</h1><p>Describe the work. ResearchFlow will use your existing writing workflow to build a strong starting point, ready for your direction.</p></section>", unsafe_allow_html=True)
        composer()
        return

    left, right = st.columns([1.5, 1], vertical_alignment="center")
    with left:
        status = "Revised draft" if mode == "revise" else "New draft"
        st.markdown(f"<div class='meta'>{status} | {word_count(draft):,} words</div>", unsafe_allow_html=True)
    with right:
        first, second = st.columns(2)
        with first:
            copy_control(draft)
        with second:
            st.download_button(
                "Download .md",
                data=draft,
                file_name=f"{re.sub(r'[^a-z0-9]+', '-', st.session_state.title.lower()).strip('-') or 'researchflow-draft'}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with st.container(border=True):
        st.markdown("<div class='document-label'>ResearchFlow draft</div>", unsafe_allow_html=True)
        st.markdown(draft)

    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<div class='eyebrow'>Revision</div><p style='margin:.1rem 0 .8rem;color:#b4aec6'>Keep the draft in view and direct the next pass.</p>", unsafe_allow_html=True)
        st.text_area(
            "Tell ResearchFlow what to change",
            key="revision",
            placeholder="Tell ResearchFlow what to change... e.g., make it shorter, improve clarity, or use a more direct tone.",
            height=86,
            label_visibility="collapsed",
        )
        _, revision_button = st.columns([3, 1])
        with revision_button:
            if st.button("Revise draft", type="primary", use_container_width=True):
                revise()

    with st.expander("Research sources"):
        sources = st.session_state.sources
        if not sources:
            st.caption("No research sources were returned for this draft.")
        for index, source in enumerate(sources, start=1):
            url = source["url"]
            title = source.get("title") or url
            domain = urlparse(url).netloc.removeprefix("www.") or "Source"
            published_date = source.get("published_date")
            st.markdown(f"**{index}. {escape(title)}**")
            st.caption(f"{domain}{f' · {published_date}' if published_date else ''}")
            st.link_button("Open source", url, key=f"source-{st.session_state.thread_id}-{index}")
            if excerpt := source.get("content"):
                st.caption(excerpt[:280] + ("…" if len(excerpt) > 280 else ""))


setup_state()
sidebar()
draft_workspace()
