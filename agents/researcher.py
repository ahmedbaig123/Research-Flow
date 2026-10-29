
import os

from dotenv import load_dotenv
from tavily import TavilyClient

from src.models import WritingRequirements, writingplan

load_dotenv()


def research_topic(
    requirements: WritingRequirements,
    plan: writingplan,
) -> dict:
    """
    Search the web when either the requirements or the plan requests research.
    Return research notes and source metadata for downstream agents.
    """

    # Research must run if either agent says it is needed.
    if not (requirements.research_required or plan.needs_research):
        print("Research skipped: this task does not require web research.")
        return {"research_notes": [], "sources": []}

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY is missing. Add it to your .env file."
        )

    tavily = TavilyClient(api_key=api_key)

    # Use the topic and planned research questions.
    queries = [requirements.topic]
    queries.extend(plan.research_questions or [])

    # Remove empty and duplicate queries while preserving order.
    unique_queries = list(
        dict.fromkeys(
            query.strip()
            for query in queries
            if query and query.strip()
        )
    )

    research_notes = []
    sources = []
    seen_urls = set()

    # Limit searches to control latency and API usage.
    for query in unique_queries[:5]:
        try:
            response = tavily.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=False,
            )
        except Exception as exc:
            print(f"Research search failed for query {query!r}: {exc}")
            continue

        for result in response.get("results", []):
            url = (result.get("url") or "").strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            title = result.get("title") or "Untitled source"
            content = result.get("content") or ""
            published_date = result.get("published_date") or ""

            source = {
                "title": title,
                "url": url,
                "content": content,
                "published_date": published_date,
            }
            sources.append(source)

            research_notes.append(
                f"Research question: {query}\n"
                f"Source title: {title}\n"
                f"URL: {url}\n"
                f"Publication date: {published_date or 'Not provided'}\n"
                f"Source excerpt: {content}"
            )

    print(f"Research notes found: {len(research_notes)}")
    print(f"Sources found: {len(sources)}")

    if not sources:
        print(
            "Warning: Research was requested, but no sources were found. "
            "The Writer should avoid unsupported specific claims."
        )

    return {
        "research_notes": research_notes,
        "sources": sources,
    }
