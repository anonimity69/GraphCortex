from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.infrastructure.db.queries.retrieval_queries import get_anchor_nodes_by_name, execute_spreading_activation_hop, get_anchors_by_vector_similarity
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

    def retrieve(self, query_terms: list):
        """
        Executes Dual-Trigger Spreading Activation.
        1. Lexical search for anchors. (Fallback to Semantic Vector Search)
        2. Spreading activation (BFS traversal) from anchors.
        3. Apply lateral inhibition (Energy decay via Fan effect).
        """
        # Step 1A: Lexical Trigger
        with get_session() as session:
            anchors = get_anchor_nodes_by_name(session, query_terms, limit=LEXICAL_ANCHOR_LIMIT)
            
            # Step 1B: Semantic Vector Fallback
            if not anchors:
                self.logger.info(f"Lexical Miss for '{query_terms}'. Initiating Semantic Vector Fallback.")
                print(f"\n[!] Lexical miss for '{query_terms}'. Activating Semantic Vector Fallback...")
                
                vector = encode_embedding(query_terms[0])
                anchors = get_anchors_by_vector_similarity(session, vector, limit=SEMANTIC_ANCHOR_LIMIT)
                
                if not anchors:
                    self.logger.warning(f"Semantic Fallback Miss for '{query_terms}'. No anchors found.")
                    return {"status": "Miss", "anchors": [], "network": [], "inhibited_hubs": []}
                else:
                    self.logger.info(f"Semantic Fallback Success! Found semantic anchors: {anchors}")
            else:
                self.logger.info(f"Lexical Hit for '{query_terms}'. Found exact anchors: {anchors}")
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
                traversed = execute_spreading_activation_hop(session, anchor["node_id"], self.max_depth)
                
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

            return {
                "status": "Hit", 
                "anchors": [a["name"] for a in anchors],
                "network": list(unique_network_dict.values()),
                "inhibited_hubs": list(set(dropped))
            }
