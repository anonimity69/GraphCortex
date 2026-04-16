# Module 05: Working Memory

## File Covered
`src/graph_cortex/core/memory/working.py`

---

## What Working Memory Does

Working Memory is the **real-time conversation buffer**. It stores the raw back-and-forth between user and agent as it happens, before any summarisation or knowledge extraction occurs.

**Graph structure it creates:**
```
(Interaction: session_abc)
    ├── [:CONTAINS] → (Message: role="user", content="How does clean architecture...")
    │                     └── [:NEXT] →
    └── [:CONTAINS] → (Message: role="agent", content="By strictly decoupling...")
```

---

## Full Code with Line-by-Line Explanation

### Imports

```python
import uuid
from datetime import datetime
from graph_cortex.infrastructure.db.neo4j_connection import get_session
```
- `uuid` — Generates globally unique identifiers for each message (e.g., `a1b2c3d4-e5f6-...`).
- `datetime` — Captures the exact timestamp when each node is created.
- `get_session` — Our Singleton Neo4j session factory from Module 03.

### Class Definition

```python
class WorkingMemory:
    """
    Handles real-time bounded interactions.
    This acts as a short-term buffer before memories are summarized into episodic 
    or semantic structures.
    """
    def __init__(self):
        pass
```
The `__init__` does nothing because `WorkingMemory` is stateless — it has no instance variables. Every operation goes directly to Neo4j. This is a deliberate Clean Architecture choice: the class is a **service**, not a data container.

---

### Method 1: `add_interaction()`

```python
    def add_interaction(self, session_id: str):
        """Creates a new Interaction session node."""
        query = """
        MERGE (i:Interaction {session_id: $session_id})
        ON CREATE SET i.timestamp = $timestamp, i.created_at = $timestamp
        RETURN i
        """
```

**Cypher breakdown:**

| Keyword | What It Does |
|---|---|
| `MERGE` | "Find or Create." If an Interaction with this `session_id` exists, reuse it. Otherwise, create it. This is **idempotent** — calling it twice with the same ID won't create a duplicate. |
| `ON CREATE SET` | Only executes the `SET` clause when a **new** node is created (not when an existing one is found). This prevents overwriting the original timestamp on subsequent calls. |
| `$session_id` | A parameterised variable. Never string-interpolated — this prevents Cypher injection attacks. |

```python
        with get_session() as session:
            session.run(query, session_id=session_id, timestamp=datetime.now().isoformat())
        return session_id
```

**`with get_session() as session`** — The context manager ensures the session is properly closed even if an exception occurs. The `session.run()` method sends the Cypher query to Neo4j with the provided parameters.

**`datetime.now().isoformat()`** — Produces `"2026-04-16T18:47:41.123456"`. ISO 8601 format is universally parseable and sorts lexicographically.

---

### Method 2: `add_message()` — The Complex One

```python
    def add_message(self, session_id: str, role: str, content: str):
        """Appends a new message to an interaction session."""
        message_id = str(uuid.uuid4())
```
Every message gets a UUID. This guarantees global uniqueness without a central counter.

```python
        query = """
        MATCH (i:Interaction {session_id: $session_id})
```
**Step 1:** Find the Interaction node for this session. If `add_interaction()` wasn't called first, this will match nothing and the entire query returns `None`.

```python
        // Find the last message to link via [:NEXT]
        OPTIONAL MATCH (i)-[:CONTAINS]->(last:Message)
        WHERE NOT (last)-[:NEXT]->()
```
**Step 2:** Find the **last** message in the chain. The logic:
- `OPTIONAL MATCH` — Try to find it, but don't fail if there are no messages yet (first message in the conversation).
- `(i)-[:CONTAINS]->(last:Message)` — Find any Message that this Interaction contains.
- `WHERE NOT (last)-[:NEXT]->()` — Filter to only the message that has **no outgoing `[:NEXT]` relationship** — i.e., it's the tail of the linked list.

If this is the first message, `last` will be `NULL`.

```python
        CREATE (m:Message {
            message_id: $message_id, 
            role: $role, 
            content: $content, 
            timestamp: $timestamp
        })
        
        CREATE (i)-[:CONTAINS]->(m)
```
**Step 3:** Create the new message node and link it to the Interaction. Every message is always linked to its parent Interaction via `[:CONTAINS]`.

```python
        // Link to the previous message if it exists (native Cypher conditional)
        WITH last, m
        FOREACH (_ IN CASE WHEN last IS NOT NULL THEN [1] ELSE [] END |
            CREATE (last)-[:NEXT]->(m)
        )
```

**Step 4: The Conditional Link.** This is the most sophisticated part. Let's break it down:

| Part | Meaning |
|---|---|
| `WITH last, m` | Carry forward both variables to the next clause |
| `CASE WHEN last IS NOT NULL THEN [1] ELSE [] END` | If `last` exists, produce a list with one element `[1]`. If `last` is NULL, produce an empty list `[]`. |
| `FOREACH (_ IN ... \| CREATE ...)` | `FOREACH` iterates over the list. If the list has one element, the `CREATE` executes once. If the list is empty, the `CREATE` never executes. |

**Why not just `IF`?**  
Cypher doesn't have a traditional `IF/ELSE` statement. The `FOREACH` + `CASE` pattern is the standard workaround for conditional writes in Cypher. Previously, we used `apoc.do.when()` for this, but that was deprecated in Neo4j 5.x.

**Result:** The first message in a conversation has no `[:NEXT]` incoming. The second message gets `(msg1)-[:NEXT]->(msg2)`. The third gets `(msg2)-[:NEXT]->(msg3)`. This creates a **singly-linked list** preserving chronological order.

```python
        RETURN m.message_id AS id
        """
```
Returns the new message's ID for confirmation.

```python
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
```

**`result.single()`** — Expects exactly one result record. Returns `None` if the query matched nothing (e.g., invalid session_id).

---

## The Graph After Two Messages

```
(Interaction: session_abc)
    │
    ├──[:CONTAINS]──→ (Message: role="user", content="How does clean architecture...")
    │                     │
    │                     └──[:NEXT]──→ (Message: role="agent", content="By strictly decoupling...")
    │                                       │
    └──[:CONTAINS]────────────────────────────┘
```

Both messages are `[:CONTAINS]` children of the Interaction, AND they're linked sequentially via `[:NEXT]`. This dual-linking gives you both:
- **Random access:** Find all messages in a session via `[:CONTAINS]`
- **Sequential access:** Walk through them in order via `[:NEXT]`
