
from graph.workflow import writing_graph


result = writing_graph.invoke({
    "user_input": "Write a blog about AI agents in 2026"
})

print("\n--- REQUIREMENTS ---")
print(result["requirements"])

print("\n--- PLAN ---")
print(result["plan"])

print("\n--- RESEARCH NOTES ---")
for note in result.get("research_notes", []):
    print(note)

print("\n--- SOURCES ---")
for source in result.get("sources", []):
    print(source["title"], "-", source["url"])
