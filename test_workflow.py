
from graph.workflow import writing_graph


config = {
    "configurable": {
        "thread_id": "researchflow-serialization-test-001"
    }
}


result = writing_graph.invoke({
    "user_input": "Write an essay about charminar"
},
config=config,)

print(result["draft"])

result = writing_graph.invoke(
    {"user_input": "Make it shorter and use a friendly tone"},
    config=config,
)

print(result["draft"])

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

print("\n--- GENERATED DRAFT ---\n")
print(result["draft"])
