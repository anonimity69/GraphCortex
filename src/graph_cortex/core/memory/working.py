import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.falkordb_connection import get_graph


class WorkingMemory:
    """Short-term interaction buffer before consolidation into episodic/semantic."""

    def add_interaction(self, session_id: str):
        query = """
        MERGE (i:Interaction {session_id: $session_id})
        ON CREATE SET i.timestamp = $timestamp, i.created_at = $timestamp, i.uid = $uid
        RETURN i.uid AS uid
        """
        graph = get_graph()
        graph.query(query, params={
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'uid': str(uuid.uuid4())
        })
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        message_id = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        query = """
        MATCH (i:Interaction {session_id: $session_id})

        OPTIONAL MATCH (i)-[:CONTAINS]->(last:Message)
        WHERE NOT (last)-[:NEXT]->()

        CREATE (m:Message {
            message_id: $message_id,
            uid: $uid,
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

        graph = get_graph()
        result = graph.query(query, params={
            'session_id': session_id,
            'message_id': message_id,
            'uid': uid,
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        if result.result_set:
            return result.result_set[0][0]
        return None
