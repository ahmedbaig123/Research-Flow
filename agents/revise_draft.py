from agents.understanding import client, MODEL

def revise_draft(previous_draft:str, user_request:str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the revision assistant for ResearchFlow AI. "
                    "Revise the supplied draft according to the user's request. "
                    "Preserve useful facts and existing source URLs. "
                    "Do not invent facts or citations. "
                    "Return only the complete revised draft."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"EXISTING DRAFT:\n{previous_draft}\n\n"
                    f"USER'S REVISION REQUEST:\n{user_request}"
                ),
            },
        ],
        temperature=0.5,
        max_completion_tokens=2500,
    )
    draft = response.choices[0].message.content

    if not draft or not draft.strip():
        raise ValueError("The revision returned an empty draft.")

    return draft.strip()