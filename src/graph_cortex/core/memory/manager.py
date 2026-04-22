from graph_cortex.core.memory.working import WorkingMemory
from graph_cortex.core.memory.episodic import EpisodicMemory
from graph_cortex.core.memory.semantic import SemanticMemory
from graph_cortex.infrastructure.storage.sharding import sharder
from typing import List, Dict

class MemoryManager:
    """
    Orchestrates the Multi-Layered Memory Framework (MLMF).
    Handles the pipeline from raw interaction -> event summarization -> semantic extraction.
    """
    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()

    def process_turn(self, session_id: str, user_input: str, agent_response: str):
        self.working.add_interaction(session_id)
        self.working.add_message(session_id, role="user", content=user_input)
        self.working.add_message(session_id, role="agent", content=agent_response)
        return True

    def consolidate_episode(self, session_id: str, generated_summary: str, extracted_entities: List[Dict]):
        # Property Shard the potentially heavy summary (Dependency Inversion to Infrastructure)
        stored_summary_ref = sharder.store(f"ep_{session_id}", generated_summary)
        
        # Create Episodic Event
        event_id = self.episodic.create_event(session_id, stored_summary_ref)
        
        # Extract into Semantic Memory layer
        for item in extracted_entities:
            # We don't have separate entity/concept props from the summarizer yet,
            # so we apply the extracted properties to the primary entity.
            props = item.get("properties", {})
            self.semantic.add_entity(item["entity"], attributes=props)
            self.semantic.add_entity(item["concept"])
            
            self.semantic.extract_from_event(
                event_id=event_id,
                entity_name=item["entity"],
                concept_name=item["concept"],
                relationship_type=item.get("relation", "RELATED_TO"),
                entity_props=props
            )
            
        return event_id
