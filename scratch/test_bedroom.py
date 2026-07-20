import asyncio
from graph_cortex.core.agents.summarizer import SummaryAgent

async def main():
    agent = SummaryAgent()
    # Replace bedroom with garage
    interaction_text = "User: so i found out that jason my friends stored his keys in a place named orilona which is a box inside his garage. keep it in memory.\nAgent: Understood. I have noted that Jason's keys are stored in a box named Orilona, which is located inside his garage."
    
    response = await agent.query_llm(user_input=interaction_text)
    print("GARAGE RESPONSE:")
    print(response)

asyncio.run(main())
