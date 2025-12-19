import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.neo4j_connection import get_session

class EpisodicMemory:
    """
    Chronological event summaries.
    Compresses working memory into discrete, searchable "events".
    """
    def __init__(self):
        pass

    def create_event(self, session_id: str, summary: str):
        """
        Creates an Event node summarizing a specific interaction session and 
        chronologically links it to the previous event.
        """
        event_id = str(uuid.uuid4())
        query = """
        MATCH (i:Interaction {session_id: $session_id})
        
        // Find the most recent event to link via a chronological chain
        OPTIONAL MATCH (latest:Event)
        WHERE NOT (latest)-[:FOLLOWS]->()
        
        CREATE (e:Event {
            event_id: $event_id,
            summary: $summary,
            timestamp: $timestamp
        })
        CREATE (e)-[:SUMMARIZES]->(i)
        
        WITH latest, e
        CALL apoc.do.when(
            latest IS NOT NULL,
            'CREATE (latest)-[:FOLLOWS]->(e) RETURN e',
            'RETURN e',
            {latest: latest, e: e}
        ) YIELD value
        
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
