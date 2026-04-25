import os
from dotenv import load_dotenv

load_dotenv()

# spreading activation
RETRIEVAL_MAX_DEPTH = int(os.getenv("RETRIEVAL_MAX_DEPTH", "3"))
RETRIEVAL_CUTOFF_THRESHOLD = float(os.getenv("RETRIEVAL_CUTOFF_THRESHOLD", "0.2"))

# lateral inhibition
INHIBITION_INITIAL_ENERGY = float(os.getenv("INHIBITION_INITIAL_ENERGY", "1.0"))
INHIBITION_DISTANCE_PENALTY = float(os.getenv("INHIBITION_DISTANCE_PENALTY", "0.5"))
INHIBITION_DEGREE_PENALTY = float(os.getenv("INHIBITION_DEGREE_PENALTY", "0.1"))

# vector search
SEMANTIC_SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_SIMILARITY_THRESHOLD", "0.65"))
SEMANTIC_ANCHOR_LIMIT = int(os.getenv("SEMANTIC_ANCHOR_LIMIT", "2"))
LEXICAL_ANCHOR_LIMIT = int(os.getenv("LEXICAL_ANCHOR_LIMIT", "5"))

# property sharding
SHARDING_MODE = os.getenv("SHARDING_MODE", "local")
SHARDING_S3_BUCKET = os.getenv("SHARDING_S3_BUCKET", "s3://ns-dmg-shard")

# defaults
DEFAULT_RELATIONSHIP_TYPE = os.getenv("DEFAULT_RELATIONSHIP_TYPE", "RELATED_TO")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
