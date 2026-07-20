import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.falkordb_connection import get_graph


class EpisodicMemory:
    """Chronological event chain. Compresses working memory into searchable events."""

    def create_event(self, session_id: str, summary: str):
        event_id = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        query = """
        MATCH (i:Interaction {session_id: $session_id})

        OPTIONAL MATCH (latest:Event {session_id: $session_id})
        WHERE NOT (latest)-[:FOLLOWS]->()

        CREATE (e:Event {
            event_id: $event_id,
            uid: $uid,
            session_id: $session_id,
            summary: $summary,
            timestamp: $timestamp
        })
        CREATE (e)-[:SUMMARIZES]->(i)

        WITH latest, e
        FOREACH (_ IN CASE WHEN latest IS NOT NULL THEN [1] ELSE [] END |
            CREATE (latest)-[:FOLLOWS]->(e)
        )

        RETURN e.event_id AS id
        """

        graph = get_graph()
        result = graph.query(query, params={
            'session_id': session_id,
            'summary': summary,
            'event_id': event_id,
            'uid': uid,
            'timestamp': datetime.now().isoformat()
        })
        if result.result_set:
            return result.result_set[0][0]
        return None
