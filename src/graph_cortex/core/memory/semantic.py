from typing import List, Dict
from graph_cortex.infrastructure.db.neo4j_connection import get_session

class SemanticMemory:
    """
    Entity-level abstractions.
    Maps out global knowledge elements derived from specific episodic events.
    """
    def __init__(self):
        pass

    def add_entity(self, name: str, node_type: str = "Entity", attributes: Dict = None):
        """Creates or updates a general semantic entity."""
        if attributes is None:
            attributes = {}
            
        query = f"MERGE (e:{node_type} {{name: $name}}) "
        if attributes:
            set_clauses = ", ".join([f"e.{k} = ${k}" for k in attributes.keys()])
            query += f"SET {set_clauses} "
        query += "RETURN e.name AS name"
        
        with get_session() as session:
            session.run(query, name=name, **attributes)
        return name

    def extract_from_event(self, event_id: str, entity_name: str, concept_name: str, relationship_type: str = "RELATED_TO"):
        """
        Extracts structured semantic knowledge from an event.
        """
        rel_type = relationship_type.upper().replace(" ", "_")
        
        query = f"""
        MATCH (ev:Event {{event_id: $event_id}})
        MERGE (e:Entity {{name: $entity_name}})
        MERGE (c:Concept {{name: $concept_name}})
        
        MERGE (e)-[:EXTRACTED_FROM]->(ev)
        MERGE (c)-[:EXTRACTED_FROM]->(ev)
        MERGE (e)-[:{rel_type}]->(c)
        """
        with get_session() as session:
            session.run(query, event_id=event_id, entity_name=entity_name, concept_name=concept_name)
        return True
