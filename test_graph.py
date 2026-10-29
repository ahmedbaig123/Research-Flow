from src.models import WritingRequirements
from graph.workflow import writing_graph

result = writing_graph.invoke({
    "requirements": WritingRequirements(
        topic="AI Agents",
        writing_type="article",
        target_length=1000,
        audience="Beginner developers",
        tone="Professional",
    ),
    "outline": [],
    "research_notes": [],
    "sources": [],
    "draft": "",
    "feedback": "",
    "revision_count": 0,
    "critic_approved": False,
    "user_approved": False,
})

print(result["draft"])