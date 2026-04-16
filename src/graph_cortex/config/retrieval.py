"""
Centralized Retrieval Engine Configuration.

Single source of truth for all retrieval tuning parameters.
All values are read from environment variables so users can tune the
Spreading Activation, Lateral Inhibition, and Semantic Fallback behaviour
without modifying any source code.

To customize, update your .env file:
    RETRIEVAL_MAX_DEPTH=3
    RETRIEVAL_CUTOFF_THRESHOLD=0.2
    ...
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Spreading Activation ───────────────────────────────────────────────────
# Maximum BFS hop depth from each anchor node.
RETRIEVAL_MAX_DEPTH = int(os.getenv("RETRIEVAL_MAX_DEPTH", "3"))

# Minimum activation energy for a node to survive Lateral Inhibition.
RETRIEVAL_CUTOFF_THRESHOLD = float(os.getenv("RETRIEVAL_CUTOFF_THRESHOLD", "0.2"))

# ─── Lateral Inhibition (Energy Decay) ──────────────────────────────────────
# Starting energy assigned to anchor nodes. Default: 1.0 (maximum).
INHIBITION_INITIAL_ENERGY = float(os.getenv("INHIBITION_INITIAL_ENERGY", "1.0"))

# How aggressively energy decays with each hop away from the anchor.
INHIBITION_DISTANCE_PENALTY = float(os.getenv("INHIBITION_DISTANCE_PENALTY", "0.5"))

# How aggressively energy decays for high-degree hub nodes.
INHIBITION_DEGREE_PENALTY = float(os.getenv("INHIBITION_DEGREE_PENALTY", "0.1"))

# ─── Semantic Vector Fallback ───────────────────────────────────────────────
# Minimum cosine similarity score to accept a vector match as a valid anchor.
SEMANTIC_SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_SIMILARITY_THRESHOLD", "0.65"))

# Maximum number of anchors returned by semantic vector search.
SEMANTIC_ANCHOR_LIMIT = int(os.getenv("SEMANTIC_ANCHOR_LIMIT", "2"))

# Maximum number of anchors returned by lexical string search.
LEXICAL_ANCHOR_LIMIT = int(os.getenv("LEXICAL_ANCHOR_LIMIT", "5"))

# ─── Property Sharding ─────────────────────────────────────────────────────
# Storage mode for heavy text properties: "local" (inline) or "s3" (external).
SHARDING_MODE = os.getenv("SHARDING_MODE", "local")

# S3 bucket URI prefix (only used when SHARDING_MODE=s3).
SHARDING_S3_BUCKET = os.getenv("SHARDING_S3_BUCKET", "s3://ns-dmg-shard")

# ─── Semantic Defaults ─────────────────────────────────────────────────────
# Default Neo4j relationship type when extracting knowledge from events.
DEFAULT_RELATIONSHIP_TYPE = os.getenv("DEFAULT_RELATIONSHIP_TYPE", "RELATED_TO")

# ─── Logging ────────────────────────────────────────────────────────────────
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
