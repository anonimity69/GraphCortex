import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

async def main():
    load_dotenv()
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = """System Instruction:
You MUST return ONLY a valid JSON object matching this exact schema:
{
  "summary": "Short 1 sentence description of the interaction",
  "entities": []
}

User Input:
User: so i found out that jason my friends stored his keys in a place named orilona which is a box inside his garage. keep it in memory.
Agent: Understood. I have noted that Jason's keys are stored in a box named Orilona, which is located inside his garage."""

    coro = client.aio.models.generate_content(
        model="gemma-4-26b-a4b-it",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=2048,
        )
    )
    response = await coro
    print("DIRECT RESPONSE DUMP:")
    print("Finish reason:", response.candidates[0].finish_reason)
    print("Text:", response.text)
    print("Usage:", response.usage_metadata)

asyncio.run(main())
