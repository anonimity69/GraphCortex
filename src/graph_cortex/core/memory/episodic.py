import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.neo4j_connection import get_session


class EpisodicMemory:
    """Chronological event chain. Compresses working memory into searchable events."""

    def create_event(self, session_id: str, summary: str):
        event_id = str(uuid.uuid4())
        query = """
        MATCH (i:Interaction {session_id: $session_id})
        
        OPTIONAL MATCH (latest:Event {session_id: $session_id})
        WHERE NOT (latest)-[:FOLLOWS]->()
        
        CREATE (e:Event {
            event_id: $event_id,
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

        with get_session() as session:
            result = session.run(
                query,
                session_id=session_id,
                summary=summary,
                event_id=event_id,
                timestamp=datetime.now().isoformat()
            )
            record = result.single()
            return record["id"] if record else None
