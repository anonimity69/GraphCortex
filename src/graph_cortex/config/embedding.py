"""
Centralized Embedding Model Configuration.

Single source of truth for the semantic embedding model used across GraphCortex.
The model name and device are read from environment variables, so users can swap
models without touching any source code.

To change the model, simply update your .env file:
    EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
    EMBEDDING_DEVICE=mps

The vector dimension is auto-detected from the loaded model, ensuring the
Neo4j vector index dimension always matches the model output.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── External Configuration (read from .env) ───────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "mps")

# ─── Lazy-Loaded Singleton Model ────────────────────────────────────────────
_model_instance = None
_vector_dimension = None


def get_model():
    """
    Returns the shared SentenceTransformer model instance.
    Lazy-loaded on first call to avoid unnecessary startup cost.
    """
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer
        print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL} (device: {EMBEDDING_DEVICE})")
        _model_instance = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
        print(f"[INFO] Model loaded. Vector dimensions: {get_vector_dimension()}")
    return _model_instance


def get_vector_dimension():
    """
    Returns the output vector dimension of the configured model.
    Auto-detected from the model architecture — never hardcoded.
    """
    global _vector_dimension
    if _vector_dimension is not None:
        return _vector_dimension

    # If the model is already loaded, read dimension directly
    global _model_instance
    if _model_instance is not None:
        _vector_dimension = _model_instance.get_sentence_embedding_dimension()
        return _vector_dimension

    # Fallback: load the model to detect dimension
    model = get_model()
    _vector_dimension = model.get_sentence_embedding_dimension()
    return _vector_dimension


def encode(text: str) -> list:
    """
    Encodes a text string into a vector embedding using the configured model.
    Returns a plain Python list of floats (compatible with Neo4j storage).
    """
    model = get_model()
    return model.encode(text, show_progress_bar=False).tolist()
