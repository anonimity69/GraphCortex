import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.neo4j_connection import get_session


class WorkingMemory:
    """Short-term interaction buffer before consolidation into episodic/semantic."""

    def add_interaction(self, session_id: str):
        query = """
        MERGE (i:Interaction {session_id: $session_id})
        ON CREATE SET i.timestamp = $timestamp, i.created_at = $timestamp
        RETURN i
        """
        with get_session() as session:
            session.run(query, session_id=session_id, timestamp=datetime.now().isoformat())
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        message_id = str(uuid.uuid4())
        query = """
        MATCH (i:Interaction {session_id: $session_id})
        
        OPTIONAL MATCH (i)-[:CONTAINS]->(last:Message)
        WHERE NOT (last)-[:NEXT]->()
        
        CREATE (m:Message {
            message_id: $message_id, 
            session_id: $session_id,
            role: $role, 
            content: $content, 
            timestamp: $timestamp
        })
        
        CREATE (i)-[:CONTAINS]->(m)
        
        WITH last, m
        FOREACH (_ IN CASE WHEN last IS NOT NULL THEN [1] ELSE [] END |
            CREATE (last)-[:NEXT]->(m)
        )
        
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
