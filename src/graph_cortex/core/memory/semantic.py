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

    def _create_composite_text(self, name: str, node_type: str, properties: Dict = None) -> str:
        """
        Creates a flat string representation of the node for vector embedding.
        Format: "NodeType: Name Key1:Value1 Key2:Value2"
        """
        prop_str = ""
        if properties:
            # Flatten only string or numeric properties to keep the embedding clean
            clean_props = {k: v for k, v in properties.items() if isinstance(v, (str, int, float, bool))}
            prop_str = " ".join([f"{k}:{v}" for k, v in sorted(clean_props.items())])
            
        return f"{node_type}: {name} {prop_str}".strip()

    def _get_embedding(self, text: str) -> List[float]:
        """Returns a vector embedding using the centrally configured model."""
        return encode_embedding(text)

    def add_entity(self, name: str, node_type: str = "Entity", attributes: Dict = None):
        """Creates or updates a general semantic entity, embedding it as a vector."""
        if attributes is None:
            attributes = {}
            
        # Use composite text for the vector trigger
        composite_text = self._create_composite_text(name, node_type, attributes)
        embedding = self._get_embedding(composite_text)
            
        query = f"MERGE (e:{node_type} {{name: $name}}) "
        
        set_statements = ["e.embedding = $embedding"]
        for k in attributes.keys():
            set_statements.append(f"e.{k} = ${k}")
            
        query += f"SET {', '.join(set_statements)} "
        query += "RETURN e.name AS name"
        
        with get_session() as session:
            session.run(query, name=name, embedding=embedding, **attributes)
        return name

    def extract_from_event(self, 
                           event_id: str, 
                           entity_name: str, 
                           concept_name: str, 
                           relationship_type: str = DEFAULT_RELATIONSHIP_TYPE,
                           entity_props: Dict = None,
                           concept_props: Dict = None):
        """
        Extracts structured semantic knowledge from an event and calculates vector embeddings.
        Now supports property injection for high-fidelity semantic linkage.
        """
        raw_rel = relationship_type.upper().replace(" ", "_")
        rel_type = re.sub(r'[^A-Z0-9_]', '', raw_rel)
        
        # Calculate composite embeddings
        e_text = self._create_composite_text(entity_name, "Entity", entity_props)
        c_text = self._create_composite_text(concept_name, "Concept", concept_props)
        
        entity_vector = self._get_embedding(e_text)
        concept_vector = self._get_embedding(c_text)
        
        query = f"""
        MATCH (ev:Event {{event_id: $event_id}})
        MERGE (e:Entity {{name: $entity_name}})
        SET e.embedding = $entity_vector
        {" ".join([f"SET e.{k} = $e_prop_{i}" for i, k in enumerate((entity_props or {}).keys())])}
        
        MERGE (c:Concept {{name: $concept_name}})
        SET c.embedding = $concept_vector
        {" ".join([f"SET c.{k} = $c_prop_{i}" for i, k in enumerate((concept_props or {}).keys())])}
        
        MERGE (e)-[:EXTRACTED_FROM]->(ev)
        MERGE (c)-[:EXTRACTED_FROM]->(ev)
        MERGE (e)-[:{rel_type}]->(c)
        """
        
        # Build parameters dictionary
        params = {
            "event_id": event_id,
            "entity_name": entity_name,
            "concept_name": concept_name,
            "entity_vector": entity_vector,
            "concept_vector": concept_vector
        }
        if entity_props:
            for i, (k, v) in enumerate(entity_props.items()):
                params[f"e_prop_{i}"] = v
        if concept_props:
            for i, (k, v) in enumerate(concept_props.items()):
                params[f"c_prop_{i}"] = v

        with get_session() as session:
            session.run(query, **params)
        return True
