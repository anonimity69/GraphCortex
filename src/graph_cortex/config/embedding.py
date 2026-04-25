import os
from dotenv import load_dotenv
import logging

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "mps")

_model_instance = None
_vector_dimension = None


def get_model():
    """Lazy-load the SentenceTransformer singleton."""
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer
        logging.info(f"Loading embedding model: {EMBEDDING_MODEL} on {EMBEDDING_DEVICE}")
        _model_instance = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
    return _model_instance


def get_vector_dimension():
    global _vector_dimension
    if _vector_dimension is not None:
        return _vector_dimension

    model = get_model()
    _vector_dimension = model.get_sentence_embedding_dimension()
    return _vector_dimension


def encode(text: str) -> list:
    return get_model().encode(text, show_progress_bar=False).tolist()
