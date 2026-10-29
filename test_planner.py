
from agents.understanding import understand_request
from agents.planner import create_plan

requests = [
    "Write a 1500-word blog about AI agents in 2026",
    "Write a recipe for chicken biryani",
    "Write a poem about missing home",
    "Write a review of the latest electric cars",
]

for request in requests:
    requirements = understand_request(request)
    plan = create_plan(requirements)

    print("\n" + "=" * 60)
    print("REQUEST:", request)
    print("\nPLAN:")
    print(plan.model_dump_json(indent=2))
