import pytest
from graph_cortex.core.retrieval.inhibition import apply_lateral_inhibition

def test_lateral_inhibition_base_energy():
    """
    Ensures a single node with no hops and zero degree retains initial energy.
    """
    nodes = [{"node_id": "1", "distance": 0, "degree": 0}]
    results, rejected = apply_lateral_inhibition(
        nodes, 
        cutoff_threshold=0.2, 
        initial_energy=1.0, 
        distance_penalty=0.5, 
        degree_penalty=0.1
    )
    assert len(results) == 1
    assert results[0]["node_id"] == "1"
    assert results[0]["activation_energy"] == 1.0
    assert len(rejected) == 0

def test_lateral_inhibition_distance_decay():
    """
    Ensures nodes exponentially lose energy over hops (distance penalty).
    """
    nodes = [{"node_id": "2", "distance": 2, "degree": 0}]
    # energy = 1.0 * e^(-0.5 * 2) = 1.0 * e^(-1) = ~0.367
    results, rejected = apply_lateral_inhibition(
        nodes, 
        cutoff_threshold=0.2, 
        initial_energy=1.0, 
        distance_penalty=0.5, 
        degree_penalty=0.1
    )
    assert len(results) == 1
    assert 0.36 < results[0]["activation_energy"] < 0.37

def test_lateral_inhibition_hub_suppression():
    """
    Ensures high-degree hubs fall below threshold and are rejected.
    """
    nodes = [{"node_id": "3", "distance": 1, "degree": 50}]
    # energy = 1.0 * e^(-0.5 * 1) * e^(-0.1 * 50) = e^(-0.5) * e^(-5) = e^-5.5 = ~0.004
    # Cutoff is 0.2, so it should be rejected.
    results, rejected = apply_lateral_inhibition(
        nodes, 
        cutoff_threshold=0.2, 
        initial_energy=1.0, 
        distance_penalty=0.5, 
        degree_penalty=0.1
    )
    assert len(results) == 0
    assert len(rejected) == 1
    assert rejected[0] == "3"
