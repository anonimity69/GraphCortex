# Module 04: Schema Migrations & Vector Indexes

## File Covered
`src/graph_cortex/infrastructure/db/schema_migrations.py`

---

## Full Code with Line-by-Line Explanation

```python
from graph_cortex.infrastructure.db.neo4j_connection import get_session
```
Imports our Singleton session factory. Every query in this file runs through the shared connection pool.

```python
# Configuration for Semantic Vector Search
# sentence-transformers (BAAI/bge-base-en-v1.5) uses 768-dimensional vectors.
# If migrating to OpenAI embeddings later, change this to 1536 and re-initialize.
VECTOR_DIMENSION = 768
```

**Why is this a module-level constant?**  
The vector dimension is a schema-level decision that affects multiple components:
1. The Neo4j vector index must be created with a specific dimension.
2. The embedding model must output vectors of that exact dimension.
3. Every query vector must also match.

By centralising it here, you change one number to switch models. For example:
- `all-MiniLM-L6-v2` → 384
- `BAAI/bge-base-en-v1.5` → 768
- `OpenAI text-embedding-3-small` → 1536

---

### The `initialize_schema()` Function

```python
def initialize_schema():
    """
    Initializes constraints and indexes for the Multi-Layer Memory Framework schema.
    """
```

This function runs once when the application starts (called from `main.py`). It's **idempotent** — running it multiple times is safe because every query uses `IF NOT EXISTS`.

#### Part 1: Base Constraints

```python
    base_queries = [
        # Working Memory Constraints
        "CREATE INDEX IF NOT EXISTS FOR (i:Interaction) ON (i.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.message_id)",
```
**Indexes** speed up lookups. When you `MATCH (i:Interaction {session_id: ...})`, Neo4j can jump directly to the right node instead of scanning every node.

- `Interaction.timestamp` — Indexed so we can quickly sort/filter interactions by time.
- `Message.message_id` — Indexed so we can quickly find specific messages.

```python
        # Episodic Memory Constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
```
**Constraints vs Indexes:**
- A **constraint** (`REQUIRE ... IS UNIQUE`) enforces data integrity. Neo4j will physically reject any attempt to create two Events with the same `event_id`. It also automatically creates an index.
- An **index** only speeds up lookups, but doesn't enforce uniqueness.

We use a constraint on `event_id` because every event must be globally unique (we generate UUIDs).

```python
        # Semantic Memory Constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE"
    ]
```
Entities and Concepts are identified by their `name` (e.g., `"Clean Architecture"`). The uniqueness constraint ensures that `MERGE (e:Entity {name: "Clean Architecture"})` either finds the existing node or creates a new one — never a duplicate.

#### Part 2: Vector Indexes (Phase 3)

```python
    vector_queries = [
        "DROP INDEX entity_vector_index IF EXISTS",
        "DROP INDEX concept_vector_index IF EXISTS",
```
**Why DROP before CREATE?**  
Vector indexes are dimension-locked. If you previously created a 384-dimensional index and now want 768, Neo4j won't let you modify it in-place. You must drop and recreate. `IF EXISTS` prevents errors if the index doesn't exist yet.

```python
        f"CREATE VECTOR INDEX entity_vector_index IF NOT EXISTS FOR (e:Entity) ON (e.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {VECTOR_DIMENSION}, `vector.similarity_function`: 'cosine'}}}}",
        f"CREATE VECTOR INDEX concept_vector_index IF NOT EXISTS FOR (c:Concept) ON (c.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {VECTOR_DIMENSION}, `vector.similarity_function`: 'cosine'}}}}"
    ]
```

**Breaking this Cypher down:**

| Part | Meaning |
|---|---|
| `CREATE VECTOR INDEX` | Creates a special index type for high-dimensional vectors |
| `entity_vector_index` | Human-readable name we reference later in queries |
| `FOR (e:Entity)` | Applies to all nodes with the `Entity` label |
| `ON (e.embedding)` | Indexes the `embedding` property (the 768-dim float array) |
| `vector.dimensions: 768` | The index expects exactly 768-dimensional vectors |
| `vector.similarity_function: 'cosine'` | Uses cosine similarity (angle between vectors) for scoring. Range: 0 (orthogonal) to 1 (identical). |

**Neo4j 5.x note:** Older documentation uses `similarity.function` (with a dot). Neo4j 5.x renamed it to `vector.similarity_function`. This was one of the compatibility fixes we made.

#### Part 3: Execution with Diagnostic Error Handling

```python
    try:
        with get_session() as session:
            # 1. Base Constraints
            for query in base_queries:
                session.run(query)
            print("[INFO] Core Database Schema initialized successfully.")
```
Runs all base constraint queries sequentially. These always work on any Neo4j 5.x instance.

```python
            # 2. Vector Diagnostic Check
            try:
                for v_query in vector_queries:
                    session.run(v_query)
                print(f"[INFO] Vector Indexes ({VECTOR_DIMENSION}-Dimensions) initialized successfully.")
            except Exception as v_err:
                print(f"\n[WARNING] Neo4j Vector Initialization Failed.")
                print(f"[DIAGNOSTIC] Your current Neo4j Container version may be outdated...")
                print(f"[DIAGNOSTIC] Inner Error: {v_err}\n")
```

**Nested try/except pattern:**  
The vector index creation is wrapped in its **own** try/except, separate from the base constraints. This means:
- If vector creation fails (e.g., old Neo4j version), the base schema is still created successfully.
- The error message specifically diagnoses the vector issue rather than a generic "schema failed."
- The application can continue running in "lexical-only" mode without vectors.

```python
    except Exception as e:
        print(f"[ERROR] Failed to initialize core schema: {e}")
```
The outer try/except catches connection-level failures (Neo4j offline, wrong password).

---

## How Vector Indexes Work Internally

When you set `e.embedding = [0.123, -0.456, ...]` on a node, Neo4j's vector index uses an **HNSW (Hierarchical Navigable Small World)** algorithm internally. Think of it as a multi-layer skip-list optimised for high-dimensional nearest-neighbor search.

When you later call `db.index.vector.queryNodes('entity_vector_index', 2, $vector)`, Neo4j uses HNSW to find the 2 closest vectors in O(log n) time, avoiding the O(n) brute-force scan.

---

## Common Client Questions

**Q: "What happens if we need to change embedding models?"**  
A: Change `VECTOR_DIMENSION` in this file, change the model string in `semantic.py` and `engine.py`, then re-run the schema migration. The DROP+CREATE pattern rebuilds the indexes cleanly. You'll also need to re-embed existing nodes (one-time batch job).

**Q: "Why cosine similarity and not Euclidean distance?"**  
A: Cosine similarity measures the *angle* between vectors, not the *magnitude*. This means "Clean Architecture" and "Software Design" will be scored similarly regardless of how long or short the original text was. Euclidean distance is sensitive to vector magnitude, which is undesirable for text embeddings.
