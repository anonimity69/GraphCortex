import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.neo4j_connection import get_session

class WorkingMemory:
    """
    Handles real-time bounded interactions.
    This acts as a short-term buffer before memories are summarized into episodic 
    or semantic structures.
    """
    def __init__(self):
        pass

    def add_interaction(self, session_id: str):
        """Creates a new Interaction session node."""
        query = """
        MERGE (i:Interaction {session_id: $session_id})
        ON CREATE SET i.timestamp = $timestamp, i.created_at = $timestamp
        RETURN i
        """
        with get_session() as session:
            session.run(query, session_id=session_id, timestamp=datetime.now().isoformat())
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """Appends a new message to an interaction session."""
        message_id = str(uuid.uuid4())
        query = """
        MATCH (i:Interaction {session_id: $session_id})
        
        // Find the last message to link via [:NEXT]
        OPTIONAL MATCH (i)-[:CONTAINS]->(last:Message)
        WHERE NOT (last)-[:NEXT]->()
        
        CREATE (m:Message {
            message_id: $message_id, 
            role: $role, 
            content: $content, 
            timestamp: $timestamp
        })
        
        CREATE (i)-[:CONTAINS]->(m)
        
        WITH last, m
        // Link to the previous message if it exists
        CALL apoc.do.when(
            last IS NOT NULL,
            'CREATE (last)-[:NEXT]->(m) RETURN m',
            'RETURN m',
            {last: last, m: m}
        ) YIELD value
        
        RETURN m.message_id AS id
        """
        
        with get_session() as session:
            result = session.run(
                query, 
                session_id=session_id, 
                message_id=message_id, 
                role=role, 
                content=content,
                timestamp=datetime.now().isoformat()
            )
            record = result.single()
            return record["id"] if record else None
