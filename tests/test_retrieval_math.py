import pytest
import math
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
    assert results[0]["activation_energy"] == pytest.approx(1.0)
    assert len(rejected) == 0

def test_lateral_inhibition_distance_decay():
    """
    Ensures nodes exponentially lose energy over hops (distance penalty).
    Formula: E = E0 * exp(-dist * p_d)
    For dist=2, p_d=0.5: E = 1.0 * exp(-1) ≈ 0.3679
    """
    nodes = [{"node_id": "2", "distance": 2, "degree": 0}]
    results, rejected = apply_lateral_inhibition(
        nodes, 
        cutoff_threshold=0.2, 
        initial_energy=1.0, 
        distance_penalty=0.5, 
        degree_penalty=0.1
    )
    assert len(results) == 1
    assert results[0]["activation_energy"] == pytest.approx(0.3679, abs=1e-3)

def test_lateral_inhibition_hub_suppression():
    """
    Ensures high-degree hubs fall below threshold and are rejected.
    Formula: E = E0 * exp(-dist * p_d) * exp(-deg * p_g)
    For dist=1, p_d=0.5, deg=50, p_g=0.1: E = exp(-0.5) * exp(-5) = exp(-5.5) ≈ 0.0041
    """
    nodes = [{"node_id": "3", "distance": 1, "degree": 50}]
    results, rejected = apply_lateral_inhibition(
        nodes, 
        cutoff_threshold=0.2, 
        initial_energy=1.0, 
        distance_penalty=0.5, 
        degree_penalty=0.1
    )
    assert len(results) == 0
    assert len(rejected) == 1
    assert rejected[0] == "UnknownHub"
