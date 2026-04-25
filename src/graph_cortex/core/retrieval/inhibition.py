import math

from graph_cortex.config.retrieval import (
    INHIBITION_INITIAL_ENERGY, INHIBITION_DEGREE_PENALTY,
    INHIBITION_DISTANCE_PENALTY, RETRIEVAL_CUTOFF_THRESHOLD
)


def apply_lateral_inhibition(traversed_nodes,
                             initial_energy=INHIBITION_INITIAL_ENERGY,
                             degree_penalty=INHIBITION_DEGREE_PENALTY,
                             distance_penalty=INHIBITION_DISTANCE_PENALTY,
                             cutoff_threshold=RETRIEVAL_CUTOFF_THRESHOLD):
    """Fan-effect energy decay. High-degree hubs get suppressed."""
    filtered = []
    dropped_hubs = []

    for node in traversed_nodes:
        deg = node.get("degree", 1)
        dist = node.get("distance", 1)

        ae = initial_energy * math.exp(-dist * distance_penalty) * math.exp(-deg * degree_penalty)
        node["activation_energy"] = round(ae, 4)

        if ae >= cutoff_threshold:
            filtered.append(node)
        else:
            dropped_hubs.append(node.get("name", "UnknownHub"))

    return filtered, dropped_hubs
