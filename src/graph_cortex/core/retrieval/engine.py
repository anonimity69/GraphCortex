import re
import heapq
import numpy as np

from graph_cortex.infrastructure.db.falkordb_connection import get_graph
from graph_cortex.infrastructure.db.queries.retrieval_queries import (
    execute_spreading_activation_hop,
    get_anchors_by_fulltext,
    get_anchors_by_vector_similarity,
    get_neighbors,
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


def _cosine_similarity(a, b):
    """Fast cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class RetrievalEngine:
    """Dual-trigger retrieval with A*-guided graph traversal.

    Retrieval flow:
    1. Find anchor nodes via BM25 fulltext + cosine vector search
    2. Expand from anchors using A* (embedding similarity as heuristic)
    3. Apply lateral inhibition to prune hub nodes
    4. Reconstruct edges between surviving nodes via shortestPath
    """

    def __init__(self, cutoff_threshold=RETRIEVAL_CUTOFF_THRESHOLD, max_depth=RETRIEVAL_MAX_DEPTH):
        self.cutoff_threshold = cutoff_threshold
        self.max_depth = max_depth
        self.logger = get_retrieval_logger()

    def _astar_expand(self, graph, anchor_uid, query_vector, session_id, max_nodes=30):
        """A* graph traversal from an anchor node using embedding similarity as heuristic.

        g_cost = number of hops from anchor (graph distance)
        h_cost = 1 - cosine_similarity(node_embedding, query_embedding)
        f_cost = g_cost_weight * g_cost + h_cost

        Nodes with embeddings more similar to the query are explored first,
        which prunes irrelevant branches early and shortens the search journey.
        """
        G_WEIGHT = 0.3  # weight for graph distance (lower = more heuristic-driven)

        # Priority queue: (f_cost, counter, node_uid)
        open_set = []
        counter = 0  # tiebreaker for heap stability
        visited = set()
        results = []

        # Start from anchor (g=0, h=0 since it's already a match)
        heapq.heappush(open_set, (0.0, counter, anchor_uid, 0))
        counter += 1

        while open_set and len(results) < max_nodes:
            f_cost, _, current_uid, g_cost = heapq.heappop(open_set)

            if current_uid in visited:
                continue
            visited.add(current_uid)

            # Don't re-add the anchor itself as a traversed node
            if g_cost > 0:
                results.append({
                    "node_id": current_uid,
                    "distance": g_cost,
                    "f_cost": f_cost,
                })

            # Stop expanding if we've gone too deep
            if g_cost >= self.max_depth:
                continue

            # Get neighbors from FalkorDB
            neighbors = get_neighbors(graph, current_uid, session_id)

            for neighbor in neighbors:
                n_uid = neighbor["node_id"]
                if n_uid in visited:
                    continue

                # g_cost: one more hop
                new_g = g_cost + 1

                # h_cost: 1 - cosine similarity to query (lower = more relevant)
                n_embedding = neighbor.get("embedding")
                if n_embedding is not None and query_vector is not None:
                    h_cost = 1.0 - _cosine_similarity(n_embedding, query_vector)
                else:
                    h_cost = 1.0  # no embedding = maximum uncertainty

                f = G_WEIGHT * new_g + h_cost

                heapq.heappush(open_set, (f, counter, n_uid, new_g))
                counter += 1

        return results

    def retrieve(self, query_terms: list, session_id: str):
        search_query = query_terms[0] if query_terms else ""

        # FalkorDB's fulltext index uses RediSearch — sanitize special chars
        bm25_safe_query = re.sub(r'[^A-Za-z0-9\s]', '', search_query).strip()

        graph = get_graph()

        bm25_anchors = []
        if bm25_safe_query:
            bm25_anchors = get_anchors_by_fulltext(graph, bm25_safe_query, session_id=session_id)

        query_vector = encode_embedding(search_query)
        semantic_anchors = get_anchors_by_vector_similarity(graph, query_vector, session_id=session_id)

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

            # A*-guided traversal: expand from anchor using embedding similarity heuristic
            astar_nodes = self._astar_expand(
                graph, anchor["node_id"], query_vector, session_id
            )

            # Convert A* results to spreading activation format for lateral inhibition
            traversed = []
            for node in astar_nodes:
                traversed.append({
                    "node_id": node["node_id"],
                    "name": node.get("name", ""),
                    "type": node.get("type", ""),
                    "distance": node["distance"],
                    "degree": 1,  # will be refined by inhibition
                })

            # If A* found nodes, use them; otherwise fall back to spreading activation
            if not traversed:
                traversed = execute_spreading_activation_hop(
                    graph, anchor["node_id"], session_id=session_id, hop_depth=self.max_depth
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
        reconstructed_edges = get_subgraph_edges(graph, node_ids, session_id=session_id)

        return {
            "status": "Hit",
            "anchors": [a["name"] for a in anchors],
            "network": list(unique_network.values()),
            "edges": reconstructed_edges,
            "inhibited_hubs": list(set(dropped))
        }
