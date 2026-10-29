
from agents.understanding import MODEL, client


def classify_request(
    user_input: str,
    previous_draft: str | None,
) -> str:
    if not previous_draft:
        return "new"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the message as 'revise' when it asks to alter, "
                    "edit, shorten, expand, reformat, translate, restyle, or "
                    "otherwise transform the existing draft, even when the "
                    "request uses novel wording. Classify it as 'new' only "
                    "when the user clearly requests a separate writing task. "
                    "Return exactly one word."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"EXISTING DRAFT:\n{previous_draft}\n\n"
                    f"NEW MESSAGE:\n{user_input}"
                ),
            },
        ],
        temperature=0,
        max_completion_tokens=5,
    )

    result = (
        response.choices[0].message.content or ""
    ).strip().lower()

    return "revise" if result == "revise" else "new"
