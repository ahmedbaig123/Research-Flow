import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from src.models import WritingRequirements

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    max_retries=5,
    timeout=60.0,
)

MODEL = os.getenv("GROQ_MODEL","openai/gpt-oss-20b")

def understand_request(user_input: str) -> WritingRequirements:
    prompt = f"""
You are the input-understanding agent for ResearchFlow AI.

Interpret the user's writing request.

Support blogs, essays, recipes, poems, reports, reviews,
stories, research papers, and other reasonable writing tasks.

Rules:
1. Preserve explicit user requirements.
2. Missing optional details are not a reason to ask questions.
3. Infer the appropriate writing type from the request.
4. Set research_required to true when factual research,
   current information, or supporting sources are needed.
5. Ask a short clarification question only when the request
   is too ambiguous to act on.
6. Do not ask questions merely because audience or tone is missing.

Return ONLY a JSON object with these fields:
topic, writing_type, target_length, audience, tone,
research_required, citation_style, clarification_needed,
clarification_question.

Use null for unknown optional strings and target_length.
Use a JSON integer for target_length when specified.
Use true or false for boolean fields.

User request:
{user_input}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You interpret writing requests and return "
                    "valid JSON matching the specified schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The model returned an empty response.")

    data = json.loads(content)

    return WritingRequirements.model_validate(data)


