import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

RAY_ADDRESS = os.getenv("RAY_ADDRESS", "auto")  # legacy, kept for compat

DEFAULT_RESEARCHER_PROMPT = os.getenv(
    "RESEARCHER_SYSTEM_PROMPT",
    "You are a Research Agent. Answer the user's question accurately. "
    "Prioritize the provided knowledge graph context if available. "
    "If context is empty, use your own knowledge so the system can learn from it."
)

DEFAULT_SUMMARIZER_PROMPT = os.getenv(
    "SUMMARIZER_SYSTEM_PROMPT",
    "You are a Summarizer Agent. Extract the core entities, concepts, and "
    "relationships from the interaction into a structured JSON format."
)
