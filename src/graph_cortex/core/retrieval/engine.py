import re

from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.infrastructure.db.queries.retrieval_queries import (
    execute_spreading_activation_hop,
    get_anchors_by_fulltext,
    get_anchors_by_vector_similarity,
    get_subgraph_edges,
)
from graph_cortex.core.retrieval.inhibition import apply_lateral_inhibition
from graph_cortex.config.logger import get_retrieval_logger
from graph_cortex.config.embedding import encode as encode_embedding
from graph_cortex.config.retrieval import (
    RETRIEVAL_MAX_DEPTH, RETRIEVAL_CUTOFF_THRESHOLD,
    SEMANTIC_ANCHOR_LIMIT, LEXICAL_ANCHOR_LIMIT,
    INHIBITION_INITIAL_ENERGY, INHIBITION_DEGREE_PENALTY, INHIBITION_DISTANCE_PENALTY
)


class RetrievalEngine:
    """Dual-trigger spreading activation over the memory graph."""

    def __init__(self, cutoff_threshold=RETRIEVAL_CUTOFF_THRESHOLD, max_depth=RETRIEVAL_MAX_DEPTH):
        self.cutoff_threshold = cutoff_threshold
        self.max_depth = max_depth
        self.logger = get_retrieval_logger()

    def retrieve(self, query_terms: list, session_id: str):
        search_query = query_terms[0] if query_terms else ""

        # Neo4j's fulltext index uses Lucene — punctuation breaks the parser
        bm25_safe_query = re.sub(r'[^A-Za-z0-9\s]', '', search_query).strip()

        with get_session() as session:
            bm25_anchors = []
            if bm25_safe_query:
                bm25_anchors = get_anchors_by_fulltext(session, bm25_safe_query, session_id=session_id)

            vector = encode_embedding(search_query)
            semantic_anchors = get_anchors_by_vector_similarity(session, vector, session_id=session_id)

            # dedup anchors, semantic wins on collision
            unique_anchors = {}
            for a in bm25_anchors:
                unique_anchors[a["node_id"]] = a
            for a in semantic_anchors:
                unique_anchors[a["node_id"]] = a

            anchors = list(unique_anchors.values())

            if not anchors:
                self.logger.warning(f"No anchors for '{search_query}'")
                return {"status": "Miss", "anchors": [], "network": [], "inhibited_hubs": []}

            self.logger.info(f"Found {len(bm25_anchors)} BM25 + {len(semantic_anchors)} semantic anchors")

            activated_network = []
            dropped = []

            for anchor in anchors:
                activated_network.append({
                    "node_id": anchor["node_id"],
                    "name": anchor["name"],
                    "type": anchor["type"],
                    "distance": 0,
                    "degree": 1,
                    "activation_energy": INHIBITION_INITIAL_ENERGY
                })

                traversed = execute_spreading_activation_hop(
                    session, anchor["node_id"], session_id=session_id, hop_depth=self.max_depth
                )

                filtered, hubs = apply_lateral_inhibition(
                    traversed,
                    initial_energy=INHIBITION_INITIAL_ENERGY,
                    degree_penalty=INHIBITION_DEGREE_PENALTY,
                    distance_penalty=INHIBITION_DISTANCE_PENALTY,
                    cutoff_threshold=self.cutoff_threshold
                )

                activated_network.extend(filtered)
                dropped.extend(hubs)

            # keep highest activation energy per node
            unique_network = {}
            for node in activated_network:
                nid = node["node_id"]
                if nid not in unique_network or node["activation_energy"] > unique_network[nid]["activation_energy"]:
                    unique_network[nid] = node

            # reconstruct edges between surviving nodes via shortestPath
            node_ids = list(unique_network.keys())
            reconstructed_edges = get_subgraph_edges(session, node_ids, session_id=session_id)

            return {
                "status": "Hit",
                "anchors": [a["name"] for a in anchors],
                "network": list(unique_network.values()),
                "edges": reconstructed_edges,
                "inhibited_hubs": list(set(dropped))
            }
