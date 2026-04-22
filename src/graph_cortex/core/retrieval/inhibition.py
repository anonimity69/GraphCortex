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
    """
    Simulates lateral inhibition and the Fan Effect computationally.
    Calculates the Activation Energy (AE) for each node using exponential decay.
    AE = initial_energy * exp(-distance * distance_penalty) * exp(-degree * degree_penalty)
    Nodes whose AE falls below the cutoff_threshold are inhibited/dropped.
    """
    filtered_nodes = []
    dropped_hubs = []
    
    for node_data in traversed_nodes:
        degree = node_data.get("degree", 1)
        distance = node_data.get("distance", 1)
        
        # Calculate Activation Energy (Exponential Decay Formula)
        activation_energy = initial_energy * math.exp(-distance * distance_penalty) * math.exp(-degree * degree_penalty)
        
        node_data["activation_energy"] = round(activation_energy, 4)
        
        if activation_energy >= cutoff_threshold:
            filtered_nodes.append(node_data)
        else:
            dropped_hubs.append(node_data.get("name", "UnknownHub"))
            
    return filtered_nodes, dropped_hubs
