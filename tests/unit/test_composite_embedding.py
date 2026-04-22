from graph_cortex.core.memory.semantic import SemanticMemory

def test_composite_text_generation():
    sm = SemanticMemory()
    
    # Test case 1: No properties
    t1 = sm._create_composite_text("Tango-Delta-Niner", "Entity")
    assert t1 == "Entity: Tango-Delta-Niner"
    
    # Test case 2: String properties
    props = {"purpose": "override protocol", "status": "active"}
    t2 = sm._create_composite_text("Tango-Delta-Niner", "Entity", props)
    # Sorted order: purpose:override protocol status:active
    assert t2 == "Entity: Tango-Delta-Niner purpose:override protocol status:active"
    
    # Test case 3: Mixed types
    props_mixed = {"id": 123, "verified": True, "note": "secret"}
    t3 = sm._create_composite_text("Tango-Delta-Niner", "Entity", props_mixed)
    # Sorted: id:123 note:secret verified:True
    assert t3 == "Entity: Tango-Delta-Niner id:123 note:secret verified:True"
    
    print("Verification Success: Composite text generation is correct and deterministic.")

if __name__ == "__main__":
    test_composite_text_generation()
