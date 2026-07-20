import asyncio
from google import genai
from google.genai import types
from graph_cortex.config.llm import GEMINI_API_KEY, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE
from graph_cortex.core.agents.summarizer import SummaryAgent

async def main():
    agent = SummaryAgent()
    user_input = "User: so i found out that jason my friends stored his keys in a place named orilona which is a box inside his garage. keep it in memory.\nAgent: Understood. I will remember this."
    full_prompt = f"System: {agent.system_prompt}\n\nUser: {user_input}"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    coro = client.aio.models.generate_content(
        model=LLM_MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS,
        )
    )
    res = await coro
    print("TEXT:", repr(res.text))
    print("PARTS:", res.candidates[0].content.parts if res.candidates else "NO CANDIDATES")
    print("FINISH REASON:", res.candidates[0].finish_reason if res.candidates else "N/A")

asyncio.run(main())
