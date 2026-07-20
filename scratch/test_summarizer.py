import asyncio
from graph_cortex.core.agents.summarizer import SummaryAgent

async def main():
    agent = SummaryAgent()
    data = await agent.extract_and_consolidate(
        "jason stored his keys in the drawer",
        "Okay, I will remember that."
    )
    print("Extracted Data:", data)

asyncio.run(main())
