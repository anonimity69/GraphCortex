import uuid
from typing import List, Dict
import re
from graph_cortex.infrastructure.db.falkordb_connection import get_graph
from graph_cortex.config.retrieval import DEFAULT_RELATIONSHIP_TYPE
from graph_cortex.config.embedding import encode as encode_embedding


class SemanticMemory:
    """Entity-level knowledge extracted from episodic events."""

    def _composite_text(self, name: str, node_type: str, properties: Dict = None) -> str:
        """Flat string for embedding: 'NodeType: Name key:val key:val'"""
        parts = [f"{node_type}: {name}"]
        if properties:
            clean = {k: v for k, v in properties.items() if isinstance(v, (str, int, float, bool))}
            parts.extend(f"{k}:{v}" for k, v in sorted(clean.items()))
        return " ".join(parts)

    def _sanitize_key(self, k: str) -> str:
        """Ensure the key is a valid Cypher property name."""
        safe = re.sub(r'[^A-Za-z0-9_]', '', str(k))
        if not safe or not safe[0].isalpha():
            safe = 'prop_' + safe
        return safe

    def _embed(self, text: str) -> List[float]:
        return encode_embedding(text)

    def add_entity(self, name: str, session_id: str, node_type: str = "Entity", attributes: Dict = None):
        if attributes is None:
            attributes = {}

        composite = self._composite_text(name, node_type, attributes)
        embedding = self._embed(composite)
        uid = str(uuid.uuid4())

        # MERGE on name+session_id, add :Searchable super-label for fulltext indexing
        query = f"MERGE (e:Searchable {{name: $name, session_id: $session_id}}) "
        query += "ON CREATE SET e.is_active = true, e.uid = $uid "
        # Add specific node type
        query += f"SET e:{node_type} "

        set_parts = ["e.embedding = $embedding"]
        sanitized_props = {}
        for k, v in attributes.items():
            safe_k = self._sanitize_key(k)
            set_parts.append(f"e.{safe_k} = ${safe_k}")
            sanitized_props[safe_k] = v

        query += f"SET {', '.join(set_parts)} "
        query += "RETURN e.name AS name"

        graph = get_graph()
        graph.query(query, params={
            'name': name,
            'session_id': session_id,
            'embedding': embedding,
            'uid': uid,
            **sanitized_props
        })
        return name

    def extract_from_event(self,
                           event_id: str,
                           session_id: str,
                           entity_name: str,
                           concept_name: str,
                           relationship_type: str = DEFAULT_RELATIONSHIP_TYPE,
                           entity_props: Dict = None,
                           concept_props: Dict = None):
        raw_rel = relationship_type.upper().replace(" ", "_")
        rel_type = re.sub(r'[^A-Z0-9_]', '', raw_rel)

        entity_vector = self._embed(self._composite_text(entity_name, "Entity", entity_props))
        concept_vector = self._embed(self._composite_text(concept_name, "Concept", concept_props))

        entity_uid = str(uuid.uuid4())
        concept_uid = str(uuid.uuid4())

        # Build dynamic SET clauses for entity and concept properties
        entity_set_parts = []
        concept_set_parts = []
        params = {
            "event_id": event_id,
            "session_id": session_id,
            "entity_name": entity_name,
            "concept_name": concept_name,
            "entity_vector": entity_vector,
            "concept_vector": concept_vector,
            "entity_uid": entity_uid,
            "concept_uid": concept_uid,
        }

        if entity_props:
            for i, (k, v) in enumerate(entity_props.items()):
                safe_k = self._sanitize_key(k)
                entity_set_parts.append(f"SET e.{safe_k} = $e_prop_{i}")
                params[f"e_prop_{i}"] = v
        if concept_props:
            for i, (k, v) in enumerate(concept_props.items()):
                safe_k = self._sanitize_key(k)
                concept_set_parts.append(f"SET c.{safe_k} = $c_prop_{i}")
                params[f"c_prop_{i}"] = v

        query = f"""
        MATCH (ev:Event {{event_id: $event_id, session_id: $session_id}})
        MERGE (e:Searchable {{name: $entity_name, session_id: $session_id}})
        ON CREATE SET e.is_active = true, e.uid = $entity_uid
        SET e:Entity
        SET e.embedding = $entity_vector
        {" ".join(entity_set_parts)}

        MERGE (c:Searchable {{name: $concept_name, session_id: $session_id}})
        ON CREATE SET c.is_active = true, c.uid = $concept_uid
        SET c:Concept
        SET c.embedding = $concept_vector
        {" ".join(concept_set_parts)}

        MERGE (e)-[:EXTRACTED_FROM]->(ev)
        MERGE (c)-[:EXTRACTED_FROM]->(ev)
        MERGE (e)-[:{rel_type}]->(c)
        """

        graph = get_graph()
        graph.query(query, params=params)
        return True
