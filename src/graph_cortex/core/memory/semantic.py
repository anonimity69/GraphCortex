from typing import List, Dict
import re
from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.config.retrieval import DEFAULT_RELATIONSHIP_TYPE
from graph_cortex.config.embedding import encode as encode_embedding

class SemanticMemory:
    """
    Entity-level abstractions.
    Maps out global knowledge elements derived from specific episodic events.
    """
    def __init__(self):
        pass

    def _get_embedding(self, text: str) -> List[float]:
        """Returns a vector embedding using the centrally configured model."""
        return encode_embedding(text)

    def add_entity(self, name: str, node_type: str = "Entity", attributes: Dict = None):
        """Creates or updates a general semantic entity, embedding it as a vector."""
        if attributes is None:
            attributes = {}
            
        embedding = self._get_embedding(name)
            
        query = f"MERGE (e:{node_type} {{name: $name}}) "
        
        set_statements = ["e.embedding = $embedding"]
        for k in attributes.keys():
            set_statements.append(f"e.{k} = ${k}")
            
        query += f"SET {', '.join(set_statements)} "
        query += "RETURN e.name AS name"
        
        with get_session() as session:
            session.run(query, name=name, embedding=embedding, **attributes)
        return name

    def extract_from_event(self, event_id: str, entity_name: str, concept_name: str, relationship_type: str = DEFAULT_RELATIONSHIP_TYPE):
        """
        Extracts structured semantic knowledge from an event and calculates vector embeddings.
        """
        raw_rel = relationship_type.upper().replace(" ", "_")
        # Cypher string injection protection: strip all non-alphanum chars except underscores
        rel_type = re.sub(r'[^A-Z0-9_]', '', raw_rel)
        
        entity_vector = self._get_embedding(entity_name)
        concept_vector = self._get_embedding(concept_name)
        
        query = f"""
        MATCH (ev:Event {{event_id: $event_id}})
        MERGE (e:Entity {{name: $entity_name}})
        SET e.embedding = $entity_vector
        
        MERGE (c:Concept {{name: $concept_name}})
        SET c.embedding = $concept_vector
        
        MERGE (e)-[:EXTRACTED_FROM]->(ev)
        MERGE (c)-[:EXTRACTED_FROM]->(ev)
        MERGE (e)-[:{rel_type}]->(c)
        """
        with get_session() as session:
            session.run(query, event_id=event_id, entity_name=entity_name, concept_name=concept_name,
                        entity_vector=entity_vector, concept_vector=concept_vector)
        return True
