import asyncio
from graph_cortex.core.agents.summarizer import SummaryAgent

async def main():
    agent = SummaryAgent()
    user_input = "User: so i found out that jason my friends stored his keys in a place named orilona which is a box inside his garage. keep it in memory.\nAgent: Understood. I will remember this."
    res = await agent.query_llm(user_input)
    print("============")
    print(res)
    print("============")

asyncio.run(main())
