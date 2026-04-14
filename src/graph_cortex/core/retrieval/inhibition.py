def apply_lateral_inhibition(traversed_nodes, initial_energy=1.0, degree_penalty=0.1, distance_penalty=0.5, cutoff_threshold=0.2):
    """
    Simulates lateral inhibition and the Fan Effect computationally.
    Calculates the Activation Energy (AE) for each node.
    AE = initial_energy / (((distance * distance_penalty) + 1) * ((degree * degree_penalty) + 1))
    Nodes whose AE falls below the cutoff_threshold are inhibited/dropped.
    """
    filtered_nodes = []
    dropped_hubs = []
    
    for node_data in traversed_nodes:
        degree = node_data.get("degree", 1)
        distance = node_data.get("distance", 1)
        
        # Calculate Activation Energy (Decay Formula)
        denominator = ((distance * distance_penalty) + 1) * ((degree * degree_penalty) + 1)
        activation_energy = initial_energy / denominator
        
        node_data["activation_energy"] = round(activation_energy, 4)
        
        if activation_energy >= cutoff_threshold:
            filtered_nodes.append(node_data)
        else:
            dropped_hubs.append(node_data.get("name", "UnknownHub"))
            
    return filtered_nodes, dropped_hubs
