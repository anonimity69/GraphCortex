from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.infrastructure.db.queries.retrieval_queries import get_anchor_nodes_by_name, execute_spreading_activation_hop
from graph_cortex.core.retrieval.inhibition import apply_lateral_inhibition

# Stub for Semantic Trigger (Will be lazy loaded to save container memory)
# from sentence_transformers import SentenceTransformer

class RetrievalEngine:
    """
    Orchestrates the Spreading Activation Retrieval process.
    Leverages Lexical/Semantic triggers to find anchors, and transverses outwards.
    """
    def __init__(self, cutoff_threshold=0.2, max_depth=3):
        self.cutoff_threshold = cutoff_threshold
        self.max_depth = max_depth
        self.semantic_model = None # Lazy load SentenceTransformer here when needed

    def retrieve(self, query_terms: list):
        """
        Executes Dual-Trigger Spreading Activation.
        1. Lexical search for anchors. (Fallback to Semantic Vector Search)
        2. Spreading activation (BFS traversal) from anchors.
        3. Apply lateral inhibition (Energy decay via Fan effect).
        """
        # Step 1A: Lexical Trigger
        with get_session() as session:
            anchors = get_anchor_nodes_by_name(session, query_terms)
            
            # Step 1B: Semantic Vector Fallback (Stub)
            if not anchors:
                print("[!] Lexical miss. Falling back to Sentence-Transformers Vector Search... (Stub)")
                # If we had a vector index:
                # if not self.semantic_model:
                #     self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2') 
                # vector = self.semantic_model.encode(query_terms[0])
                # anchors = get_anchors_by_vector_similarity(session, vector)
                
                return {"status": "Miss", "anchors": [], "network": [], "inhibited_hubs": []}
                
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
                    "activation_energy": 1.0 # Max energy for exact match anchor
                })
                
                # Traverse outwards (Fan out) up to depth limit
                traversed = execute_spreading_activation_hop(session, anchor["node_id"], self.max_depth)
                
                # Step 3: Apply Lateral Inhibition (Energy Decay)
                filtered, hubs = apply_lateral_inhibition(
                    traversed, 
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
