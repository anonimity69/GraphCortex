import pytest
import math
from graph_cortex.core.retrieval.inhibition import apply_lateral_inhibition


def test_base_energy_preserved():
    nodes = [{"node_id": "1", "distance": 0, "degree": 0}]
    results, rejected = apply_lateral_inhibition(
        nodes, cutoff_threshold=0.2, initial_energy=1.0,
        distance_penalty=0.5, degree_penalty=0.1
    )
    assert len(results) == 1
    assert results[0]["activation_energy"] == pytest.approx(1.0)
    assert rejected == []


def test_distance_decay():
    """dist=2, penalty=0.5 => E = exp(-1) ≈ 0.3679"""
    nodes = [{"node_id": "2", "distance": 2, "degree": 0}]
    results, _ = apply_lateral_inhibition(
        nodes, cutoff_threshold=0.2, initial_energy=1.0,
        distance_penalty=0.5, degree_penalty=0.1
    )
    assert len(results) == 1
    assert results[0]["activation_energy"] == pytest.approx(0.3679, abs=1e-3)


def test_hub_suppression():
    """degree=50 should kill the node"""
    nodes = [{"node_id": "3", "distance": 1, "degree": 50}]
    results, rejected = apply_lateral_inhibition(
        nodes, cutoff_threshold=0.2, initial_energy=1.0,
        distance_penalty=0.5, degree_penalty=0.1
    )
    assert results == []
    assert len(rejected) == 1
