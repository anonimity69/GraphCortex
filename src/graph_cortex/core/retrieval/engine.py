from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.infrastructure.db.queries.retrieval_queries import execute_spreading_activation_hop
from graph_cortex.core.retrieval.inhibition import apply_lateral_inhibition
from graph_cortex.config.logger import get_retrieval_logger
from graph_cortex.config.embedding import encode as encode_embedding
from graph_cortex.config.retrieval import (
    RETRIEVAL_MAX_DEPTH, RETRIEVAL_CUTOFF_THRESHOLD,
    SEMANTIC_ANCHOR_LIMIT, LEXICAL_ANCHOR_LIMIT,
    INHIBITION_INITIAL_ENERGY, INHIBITION_DEGREE_PENALTY, INHIBITION_DISTANCE_PENALTY
)

class RetrievalEngine:
    """
    Orchestrates the Spreading Activation Retrieval process.
    Leverages Lexical/Semantic triggers to find anchors, and transverses outwards.
    """
    def __init__(self, cutoff_threshold=RETRIEVAL_CUTOFF_THRESHOLD, max_depth=RETRIEVAL_MAX_DEPTH):
        self.cutoff_threshold = cutoff_threshold
        self.max_depth = max_depth
        self.logger = get_retrieval_logger()

    def retrieve(self, query_terms: list, session_id: str):
        """
        Executes Dual-Trigger Spreading Activation.
        1. Hybrid Anchor Search (Parallel BM25 Fulltext + Semantic Vector Match)
        2. Spreading activation (BFS traversal) from anchors.
        3. Apply lateral inhibition (Energy decay via Fan effect).
        """
        import re
        search_query = query_terms[0] if query_terms else ""
        
        # Strip punctuation to prevent Neo4j Lucene syntax errors during BM25 parsing
        bm25_safe_query = re.sub(r'[^A-Za-z0-9\s]', '', search_query).strip()
        
        # Step 1: Hybrid Trigger
        with get_session() as session:
            # 1A: Fulltext BM25 Search
            bm25_anchors = []
            if bm25_safe_query:
                # Imports inside retrieve to avoid circular dependencies if any
                from graph_cortex.infrastructure.db.queries.retrieval_queries import get_anchors_by_fulltext, get_anchors_by_vector_similarity
                bm25_anchors = get_anchors_by_fulltext(session, bm25_safe_query, session_id=session_id)
            
            # 1B: Dense Vector Semantic Search
            from graph_cortex.infrastructure.db.queries.retrieval_queries import get_anchors_by_vector_similarity
            vector = encode_embedding(search_query)
            semantic_anchors = get_anchors_by_vector_similarity(session, vector, session_id=session_id)
            
            # Combine and deduplicate anchors by node_id
            unique_anchors = {}
            for a in bm25_anchors:
                unique_anchors[a["node_id"]] = a
            for a in semantic_anchors:
                unique_anchors[a["node_id"]] = a
                
            anchors = list(unique_anchors.values())
            
            if not anchors:
                self.logger.warning(f"Hybrid Search Miss for '{search_query}'. No anchors found.")
                return {"status": "Miss", "anchors": [], "network": [], "inhibited_hubs": []}
            else:
                self.logger.info(f"Hybrid Search Success! Found ({len(bm25_anchors)} BM25, {len(semantic_anchors)} Semantic) unique anchors: {anchors}")
            # Step 2: Spreading Activation from Anchors
            activated_network = []
            dropped = []
            
            for anchor in anchors:
                # Add the anchor itself to the network with maximum energy
                activated_network.append({
                    "node_id": anchor["node_id"],
                    "name": anchor["name"],
                    "type": anchor["type"],
                    "distance": 0,
                    "degree": 1,
                    "activation_energy": INHIBITION_INITIAL_ENERGY
                })
                
                # Traverse outwards (Fan out) up to depth limit
                traversed = execute_spreading_activation_hop(session, anchor["node_id"], session_id=session_id, hop_depth=self.max_depth)
                
                # Step 3: Apply Lateral Inhibition (Energy Decay)
                filtered, hubs = apply_lateral_inhibition(
                    traversed,
                    initial_energy=INHIBITION_INITIAL_ENERGY,
                    degree_penalty=INHIBITION_DEGREE_PENALTY,
                    distance_penalty=INHIBITION_DISTANCE_PENALTY,
                    cutoff_threshold=self.cutoff_threshold
                )
                
                activated_network.extend(filtered)
                dropped.extend(hubs)

            # Deduplicate by node_id, keeping the highest activation energy
            unique_network_dict = {}
            for node in activated_network:
                n_id = node["node_id"]
                if n_id not in unique_network_dict or node["activation_energy"] > unique_network_dict[n_id]["activation_energy"]:
                    unique_network_dict[n_id] = node

            # Step 4: Sub-Graph Edge Reconstruction
            # We explicitly fetch relationships between the final set of nodes.
            node_ids = list(unique_network_dict.keys())
            from graph_cortex.infrastructure.db.queries.retrieval_queries import get_subgraph_edges
            reconstructed_edges = get_subgraph_edges(session, node_ids, session_id=session_id)

            return {
                "status": "Hit", 
                "anchors": [a["name"] for a in anchors],
                "network": list(unique_network_dict.values()),
                "edges": reconstructed_edges,
                "inhibited_hubs": list(set(dropped))
            }
