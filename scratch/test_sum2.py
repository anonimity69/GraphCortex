import asyncio
from graph_cortex.core.agents.summarizer import SummaryAgent

async def main():
    agent = SummaryAgent()
    interaction_text = "User: so i found out that jason my friends stored his keys in a place named orilona which is a box inside his bedroom. keep it in memory.\nAgent: Understood. I have noted that Jason's keys are stored in a box named Orilona, which is located inside his bedroom."
    llm_response = await agent.query_llm(user_input=interaction_text)
    print("LLM RESPONSE RAW:")
    print(llm_response)

asyncio.run(main())
