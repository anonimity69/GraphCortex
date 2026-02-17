"""
Centralized LLM Configuration.

Single source of truth for the LLM settings used across GraphCortex agents.
The model name, API key, and system prompts are read from environment variables,
ensuring zero hardcoding of sensitive or tunable parameters.

To change the configuration, update your .env file:
    GEMINI_API_KEY=your_key_here
    LLM_MODEL=your_model_path
    RAY_ADDRESS=auto
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Credentials ────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─── LLM Tunables ───────────────────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL")  # No default, forcing env configuration
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ─── Ray Configuration ──────────────────────────────────────────────────────
RAY_ADDRESS = os.getenv("RAY_ADDRESS", "auto")

# ─── Default System Prompts ─────────────────────────────────────────────────
DEFAULT_RESEARCHER_PROMPT = os.getenv(
    "RESEARCHER_SYSTEM_PROMPT", 
    "You are a Research Agent. Answer the user's question accurately. Prioritize the provided knowledge graph context if available. If the provided context is empty or insufficient, you MUST use your own general knowledge to generate a comprehensive answer so the system can learn from it."
)

DEFAULT_SUMMARIZER_PROMPT = os.getenv(
    "SUMMARIZER_SYSTEM_PROMPT",
    "You are a Summarizer Agent. Extract the core entities, concepts, and relationships from the interaction into a structured JSON format."
)
