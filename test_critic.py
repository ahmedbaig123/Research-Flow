
from agents.understanding import understand_request
from agents.planner import create_plan
from agents.researcher import research_topic
from agents.writer import write_draft
from agents.critic import review_draft


request = "Write a blog about Increase of laptop prices in 2026"

requirements = understand_request(request)
plan = create_plan(requirements)

research_result = research_topic(requirements, plan)

draft = write_draft(
    requirements=requirements,
    plan=plan,
    research_notes=research_result["research_notes"],
)

feedback = review_draft(
    requirements=requirements,
    plan=plan,
    draft=draft,
    research_notes=research_result["research_notes"],
)

print("\n--- CRITIC APPROVED ---")
print(feedback.approved)

print("\n--- OVERALL FEEDBACK ---")
print(feedback.overall_feedback)

print("\n--- ISSUES ---")
for issue in feedback.issues:
    print("-", issue)

print("\n--- REVISION INSTRUCTIONS ---")
print(feedback.revision_instructions)
