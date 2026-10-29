from agents.understanding import understand_request
from agents.planner import create_plan
from agents.writer import write_draft

request = "Write a short poem about missing home"

requirements = understand_request(request)
plan = create_plan(requirements)

draft = write_draft(
    requirements=requirements,
    plan=plan,
    research_notes=[],
)

print("\n--- GENERATED DRAFT ---\n")
print(draft)