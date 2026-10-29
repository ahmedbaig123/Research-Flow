from agents.understanding import understand_request

requests = [
    "Write a 1500-word blog about AI agents in 2026",
    "Write a recipe for chicken biryani",
    "Write a poem about missing home",
]

for request in requests:
    result = understand_request(request)

    print("\nUSER:", request)
    print(result.model_dump())
