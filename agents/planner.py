
import json

from agents.understanding import client, MODEL
from src.models import WritingRequirements, writingplan


def create_plan(
    requirements: WritingRequirements,
) -> writingplan:

    prompt = f"""
You are the planning agent for ResearchFlow AI.

Create a useful plan for the user's writing task.

USER REQUIREMENTS:
{requirements.model_dump_json(indent=2)}

RULES:
1. Follow the user's explicit requirements.
2. Choose a structure suited to the requested document type.
3. Do not use generic article headings for every task.
4. Recipes need appropriate cooking instructions and ingredients.
5. Poems need a creative direction, not mandatory article sections.
6. Reviews need criteria relevant to the item being reviewed.
7. Academic papers need a logical research structure.
8. Do not invent facts, sources, or research findings.
9. If research is needed, provide specific research questions.
10. If research is not needed, leave research_questions empty.
11. Respect the requested length when one is provided.
12. Keep the plan focused on the user's actual request.

Return a valid JSON object with ALL of these exact keys:

{{
    "document_type": "string",
    "purpose": "string",
    "structure": ["string"],
    "writing_instructions": "string",
    "research_questions": ["string"],
    "needs_research": false,
    "citation_requirements": null
}}

Every key is required. Do not omit any key.
Use an empty list when there are no research questions.
Use null when citation requirements do not apply.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful writing planner. "
                    "Return valid JSON matching the requested fields."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The planner returned an empty response.")

    data = json.loads(content)

    return writingplan.model_validate(data)
