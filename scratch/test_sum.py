import asyncio
from graph_cortex.core.agents.summarizer import SummaryAgent

async def main():
    agent = SummaryAgent()
    data = await agent.extract_and_consolidate(
        "so i found out that jason my friends stored his keys in a place named orilona which is a box inside his bedroom. keep it in memory.",
        "Understood. I have noted that Jason's keys are stored in a box named Orilona, which is located inside his bedroom."
    )
    print("FINAL PARSED DATA:", data)

asyncio.run(main())
