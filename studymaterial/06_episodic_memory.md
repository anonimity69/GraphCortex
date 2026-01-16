# Module 06: Episodic Memory

## File Covered
`src/graph_cortex/core/memory/episodic.py`

---

## What Episodic Memory Does

Episodic Memory compresses raw conversations into **discrete, searchable events**. Instead of storing every message forever, a summary is created: *"User asked about Clean Architecture; agent explained decoupling."* Events are chained chronologically via `[:FOLLOWS]` to create a strict timeline.

**Graph structure it creates:**
```
(Event_001: "User asked about Clean Architecture...")
    ├── [:SUMMARIZES] → (Interaction: session_abc)
    └── [:FOLLOWS] → (Event_002: "User discussed Neo4j indexes...")
                           └── [:FOLLOWS] → (Event_003: ...)
```

---

## Full Code with Line-by-Line Explanation

```python
import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.neo4j_connection import get_session
```
Same imports as Working Memory. The pattern is consistent across all memory layers.

```python
class EpisodicMemory:
    """
    Chronological event summaries.
    Compresses working memory into discrete, searchable "events".
    """
    def __init__(self):
        pass
```
Again, stateless service. No instance variables.

---

### The `create_event()` Method

```python
    def create_event(self, session_id: str, summary: str):
        """
        Creates an Event node summarizing a specific interaction session and 
        chronologically links it to the previous event.
        """
        event_id = str(uuid.uuid4())
```
Generates a unique ID for this event (e.g., `"45a3e13b-a356-41b2-a533-a150efdb9346"`).

```python
        query = """
        MATCH (i:Interaction {session_id: $session_id})
```
**Step 1:** Find the Interaction session that this event will summarise. This is the bridge between Working Memory and Episodic Memory.

```python
        // Find the most recent event to link via a chronological chain.
        OPTIONAL MATCH (latest:Event)
        WHERE NOT (latest)-[:FOLLOWS]->()
```
**Step 2:** Find the "tail" of the event chain — the most recent event that doesn't yet have a `[:FOLLOWS]` outgoing relationship.

**Critical insight:** `OPTIONAL MATCH (latest:Event)` searches **all** Event nodes in the entire database (not just ones related to this session). This means the chronological chain spans across ALL sessions. This is intentional — it creates a single global timeline of everything the AI has ever experienced.

If this is the very first event ever created, `latest` will be `NULL`.

```python
        CREATE (e:Event {
            event_id: $event_id,
            summary: $summary,
            timestamp: $timestamp
        })
        CREATE (e)-[:SUMMARIZES]->(i)
```
**Step 3:** Create the Event node and link it to its source Interaction via `[:SUMMARIZES]`. This preserves **provenance** — you can always trace a high-level summary back to the raw conversation that generated it.

```python
        // Chronologically chain to previous event (native Cypher conditional)
        WITH latest, e
        FOREACH (_ IN CASE WHEN latest IS NOT NULL THEN [1] ELSE [] END |
            CREATE (latest)-[:FOLLOWS]->(e)
        )
```
**Step 4:** The same `FOREACH` + `CASE` conditional pattern from Working Memory. If a previous event exists, chain it: `(Event_old)-[:FOLLOWS]->(Event_new)`. If this is the first event, skip.

```python
        RETURN e.event_id AS id
        """
```

```python
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
```
Returns the newly created event's UUID for downstream use (e.g., Semantic Memory needs it to link entities back to this event).

---

## The Chronological Chain

After 3 sessions over 3 days:

```
(Event: April 14, "User discussed Clean Architecture")
    │
    └──[:FOLLOWS]──→ (Event: April 15, "User explored Neo4j indexes")
                         │
                         └──[:FOLLOWS]──→ (Event: April 16, "User upgraded embedding model")
```

This gives the AI the ability to:
- **Recall recent events:** Walk backwards through `[:FOLLOWS]` chain.
- **Understand temporal relationships:** "Clean Architecture was discussed BEFORE Neo4j indexes."
- **Answer temporal queries:** "What did we talk about yesterday?"

---

## Relationship Between Working and Episodic Memory

```
Working Memory (raw)                    Episodic Memory (compressed)
─────────────────────                   ─────────────────────────────
(Interaction: session_abc)              (Event: "User asked about 
    ├── Message: "How does..."              Clean Architecture...")
    └── Message: "By strictly..."              │
                                               └── [:SUMMARIZES] → (Interaction: session_abc)
```

The `[:SUMMARIZES]` relationship is the bridge. You can always "drill down" from a high-level event summary back into the raw messages. This is how the system supports both:
- **Fast, high-level overview:** Query the Event chain
- **Deep, detailed inspection:** Follow `[:SUMMARIZES]` → `[:CONTAINS]` → Messages

---

## Common Client Questions

**Q: "Who generates the summary?"**  
A: In the current implementation, the summary is provided by the caller (typically an LLM). The `MemoryManager.consolidate_episode()` method receives the summary as a parameter. In production, you'd call GPT/Claude to generate this summary from the raw messages.

**Q: "What if the chain breaks — two events are created simultaneously?"**  
A: The `OPTIONAL MATCH (latest:Event) WHERE NOT (latest)-[:FOLLOWS]->()` pattern finds the tail. If a race condition occurs, both new events would chain to the same predecessor, creating a fork. For a production system, you'd add a transaction lock or use a sequential queue.
