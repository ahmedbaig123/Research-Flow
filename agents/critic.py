
import re

from agents.understanding import client, MODEL
from src.models import WritingRequirements, writingplan, CriticFeedback


def review_draft(
    requirements: WritingRequirements,
    plan: writingplan,
    draft: str,
    research_notes: list[str],
) -> CriticFeedback:

    research_context = "\n\n".join(research_notes[:4])[:3000]

    if not research_context:
        research_context = "No research notes were provided."

    prompt = f"""
You are the quality reviewer for ResearchFlow AI.

USER REQUIREMENTS:
{requirements.model_dump_json()}

WRITING PLAN:
{plan.model_dump_json()}

AVAILABLE RESEARCH:
{research_context}

DRAFT:
{draft[:7000]}

Review the draft fairly.

Check:
1. Does it satisfy the user's main request?
2. Does it use the requested format, tone, and audience?
3. Is it clear, coherent, and useful?
4. Are important factual claims supported when research is required?
5. Are there serious fabricated examples, statistics, or claims?
6. Are citations required for this task?

Approval rules:
- APPROVED: YES if the draft meets the main requirements and has no
  serious problems.
- APPROVED: NO only if a serious issue materially affects accuracy,
  usefulness, or compliance.
- Do not reject a draft for minor stylistic issues.
- Do not demand citations for creative work or tasks that do not need them.
- Do not assume a claim is false only because the provided research
  does not mention it.
- Identify uncertainty rather than claiming unsupported information is false.
- List no more than 3 important issues.

Return plain text using exactly this format:

APPROVED: YES or NO
OVERALL_FEEDBACK: A brief summary in 1-2 sentences
ISSUE: First important issue, if any
ISSUE: Second important issue, if any
REVISION_INSTRUCTIONS: Concise suggestions for improvement

Do not return JSON. Do not use Markdown code fences.
If there are no important issues, omit the ISSUE lines.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a fair and practical writing reviewer. "
                    "Follow the requested plain-text output format exactly."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_completion_tokens=1000,
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        raise ValueError(
            "Critic returned an empty response. "
            f"Finish reason: {response.choices[0].finish_reason}"
        )

    # Extract the approval decision.
    approval_match = re.search(
        r"^\s*APPROVED\s*:\s*(YES|NO)\b",
        content,
        re.IGNORECASE | re.MULTILINE,
    )

    if not approval_match:
        raise ValueError(
            "Critic did not provide a valid approval decision. "
            f"Response: {content[:500]}"
        )

    approved = approval_match.group(1).upper() == "YES"

    # Extract overall feedback.
    feedback_match = re.search(
        r"^\s*OVERALL_FEEDBACK\s*:\s*(.*)",
        content,
        re.IGNORECASE | re.MULTILINE,
    )

    overall_feedback = (
        feedback_match.group(1).strip()
        if feedback_match
        else "The Critic completed its review."
    )

    # Extract individual issues.
    issues = re.findall(
        r"^\s*ISSUE\s*:\s*(.+)",
        content,
        re.IGNORECASE | re.MULTILINE,
    )
    issues = [issue.strip() for issue in issues[:3]]

    # Extract revision instructions.
    instructions_match = re.search(
        r"^\s*REVISION_INSTRUCTIONS\s*:\s*(.*)",
        content,
        re.IGNORECASE | re.MULTILINE,
    )

    revision_instructions = (
        instructions_match.group(1).strip()
        if instructions_match
        else "No specific changes requested."
    )

    return CriticFeedback(
        approved=approved,
        overall_feedback=overall_feedback,
        issues=issues,
        revision_instructions=revision_instructions,
    )
