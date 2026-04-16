from typing import List, Dict
from graph_cortex.infrastructure.db.neo4j_connection import get_session

class SemanticMemory:
    """
    Entity-level abstractions.
    Maps out global knowledge elements derived from specific episodic events.
    """
    def __init__(self):
        self.semantic_model = None

    def _get_embedding(self, text: str) -> List[float]:
        """Lazy loads SentenceTransformer using Apple Silicon MPS and returns a 768-dimensional vector."""
        if not self.semantic_model:
            from sentence_transformers import SentenceTransformer
            self.semantic_model = SentenceTransformer('BAAI/bge-base-en-v1.5', device='mps')
        return self.semantic_model.encode(text).tolist()

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

    def extract_from_event(self, event_id: str, entity_name: str, concept_name: str, relationship_type: str = "RELATED_TO"):
        """
        Extracts structured semantic knowledge from an event and calculates vector embeddings.
        """
        rel_type = relationship_type.upper().replace(" ", "_")
        
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
