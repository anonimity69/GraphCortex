import asyncio
from graph_cortex.infrastructure.inference.llm_client import LLMClient

async def main():
    client = LLMClient()
    prompt = """
Extract all entities from the following interaction. For each entity, provide its Concept, its Relation, and any Properties (like locations, details).
Output ONLY in this EXACT text format, one per line:
[ENTITY] name | [CONCEPT] type | [RELATION] relation | [PROPERTIES] key=value; key2=value2

User: so i found out that jason my friends stored his keys in a place named orilona which is a box inside his bedroom. keep it in memory.
Agent: Understood. I have noted that Jason's keys are stored in a box named Orilona, which is located inside his bedroom.
"""
    try:
        coro = client.client.aio.models.generate_content(
            model=client.model,
            contents=prompt,
        )
        response = await asyncio.wait_for(coro, timeout=30.0)
        print("Finish Reason:", response.candidates[0].finish_reason if response.candidates else "No candidates")
        print("Text:", response.text)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
