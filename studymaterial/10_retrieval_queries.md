# Module 10: Retrieval Queries (Raw Cypher)

## File Covered
`src/graph_cortex/infrastructure/db/queries/retrieval_queries.py`

---

## Why This File Exists Separately

In Clean Architecture, the **infrastructure layer** contains all database-specific code. The `RetrievalEngine` (core) doesn't write Cypher — it calls functions in this file and receives plain Python dictionaries back. If you migrate from Neo4j to AWS Neptune (which uses Gremlin instead of Cypher), you only rewrite this file.

---

## Query 1: `get_anchor_nodes_by_name()` — The Lexical Trigger

```python
def get_anchor_nodes_by_name(session, entity_names, limit=5):
    """
    Finds anchor nodes (Entities or Concepts) matching specific string names.
    This acts as the Lexical (BM25-style) trigger in the Dual-Trigger initialization.
    """
```

```python
    query = """
    UNWIND $names AS name
    MATCH (n) WHERE (n:Entity OR n:Concept) AND toLower(n.name) CONTAINS toLower(name)
    RETURN elementId(n) AS node_id, n.name AS name, labels(n)[0] AS type
    LIMIT $limit
    """
```

**Cypher breakdown:**

| Line | What It Does |
|---|---|
| `UNWIND $names AS name` | Takes the input list `["System Design", "Clean Architecture"]` and iterates over it, processing each term one at a time. |
| `MATCH (n)` | Find any node `n` in the database. |
| `WHERE (n:Entity OR n:Concept)` | Filter to only Entity and Concept nodes. Ignore Message, Event, Interaction nodes. |
| `AND toLower(n.name) CONTAINS toLower(name)` | **Case-insensitive substring matching.** `"clean architecture"` matches `"Clean Architecture"`. This is the "lexical" trigger — pure string matching, no ML. |
| `elementId(n) AS node_id` | Returns Neo4j's internal element ID (used for subsequent traversal). |
| `labels(n)[0] AS type` | Returns the node's first label (`"Entity"` or `"Concept"`). |
| `LIMIT $limit` | Cap results to prevent returning thousands of matches. |

```python
    result = session.run(query, names=entity_names, limit=limit)
    return [record.data() for record in result]
```
Converts Neo4j records to Python dicts: `[{"node_id": "4:abc:7", "name": "Clean Architecture", "type": "Entity"}]`

**When this query FAILS to find matches** (lexical miss), the Retrieval Engine falls back to semantic vector search.

---

## Query 2: `execute_spreading_activation_hop()` — The BFS Traversal

```python
def execute_spreading_activation_hop(session, target_node_id, hop_depth):
    """
    Executes a custom Cypher BFS traversal from the target node up to a certain depth.
    Calculates raw 'degree' for downstream fan-effect attenuation.
    Note: Neo4j 5.x does not allow parameters in variable-length patterns,
    so hop_depth is safely interpolated as an integer literal.
    """
    depth = int(hop_depth)  # Sanitize to prevent injection
```
**Security:** `int()` ensures only an integer value is used. If someone somehow passes `"3; DROP DATABASE"`, `int()` throws a `ValueError` before it reaches Neo4j.

```python
    query = f"""
    MATCH path = (start)-[*1..{depth}]-(connected)
    WHERE elementId(start) = $node_id
```

**Line-by-line:**

| Part | Meaning |
|---|---|
| `MATCH path = (start)-[*1..{depth}]-(connected)` | Find all paths from `start` to any `connected` node, following between 1 and `{depth}` relationships (default: 3). The `-` (no arrow) means **any direction** — both incoming and outgoing relationships. |
| `path = ...` | Assigns the entire path to a variable so we can calculate distance from it. |
| `[*1..3]` | Variable-length relationship pattern. `*1..3` means "at least 1 hop, at most 3 hops." |
| `elementId(start) = $node_id` | Start from the specific anchor node identified by its element ID. |

```python
    WITH start, connected, REDUCE(s = 0, n IN nodes(path) | s + 1) AS distance,
         COUNT { (connected)--() } AS degree
```

| Part | Meaning |
|---|---|
| `REDUCE(s = 0, n IN nodes(path) \| s + 1)` | Counts the number of nodes in the path. This is the **distance** from the anchor. A node 2 hops away has `distance = 3` (start + 2 intermediate + target). |
| `COUNT { (connected)--() }` | **Neo4j 5.x syntax.** Counts how many relationships the connected node has (its **degree**). High-degree nodes are "hubs" — they connect to many things and should be penalised. |

**Why `COUNT { }` instead of `SIZE()`?**  
Neo4j 5.x deprecated `SIZE((pattern))` for non-boolean contexts. The new `COUNT { pattern }` subquery syntax is the modern replacement.

```python
    RETURN 
        elementId(connected) AS node_id, 
        connected.name AS name, 
        labels(connected)[0] AS type,
        distance,
        degree
    ORDER BY distance ASC
    """
    result = session.run(query, node_id=target_node_id)
    return [record.data() for record in result]
```

Returns a list of dictionaries, sorted by distance (closest nodes first):
```python
[
    {"node_id": "4:abc:8", "name": "Software Design", "type": "Concept", "distance": 2, "degree": 4},
    {"node_id": "4:abc:9", "name": "Neo4j Driver", "type": "Entity", "distance": 3, "degree": 2},
    ...
]
```

The `distance` and `degree` values are passed to the Lateral Inhibition formula to calculate activation energy.

---

## Query 3: `get_anchors_by_vector_similarity()` — The Semantic Vector Fallback

```python
def get_anchors_by_vector_similarity(session, vector, limit=2):
    """
    Finds anchor nodes based on semantic vector similarity (Cosine).
    Queries the 'entity_vector_index' initialized in schema_migrations.
    """
    query = """
    CALL db.index.vector.queryNodes('entity_vector_index', $limit, $vector)
    YIELD node, score
    WHERE score > 0.65
    RETURN elementId(node) AS node_id, node.name AS name, labels(node)[0] AS type, score
    ORDER BY score DESC
    """
```

**Line-by-line:**

| Part | Meaning |
|---|---|
| `CALL db.index.vector.queryNodes(...)` | Neo4j's native vector search procedure. Takes the index name, the number of results, and the query vector. |
| `'entity_vector_index'` | References the index created in `schema_migrations.py`. |
| `$limit` | How many nearest neighbors to return (default: 2). |
| `$vector` | The 768-dimensional query vector (computed from the user's search term). |
| `YIELD node, score` | The procedure returns the matched node and its cosine similarity score (0-1). |
| `WHERE score > 0.65` | **Similarity threshold.** Filters out weak matches. 0.65 means the vectors must share at least 65% cosine similarity. This prevents the engine from "hallucinating" irrelevant anchors. |
| `ORDER BY score DESC` | Best matches first. |

```python
    result = session.run(query, limit=limit, vector=vector)
    return [record.data() for record in result]
```

Returns:
```python
[
    {"node_id": "4:abc:7", "name": "Software Design", "type": "Entity", "score": 0.9484},
    {"node_id": "4:abc:6", "name": "Clean Architecture", "type": "Entity", "score": 0.8224}
]
```

---

## How All Three Queries Connect

```
User query: ["System Design"]
                │
                ▼
    ┌── get_anchor_nodes_by_name() ──┐
    │   "System Design" CONTAINS?    │
    │   Result: [] (empty - no match)│
    └────────────┬───────────────────┘
                 │ MISS
                 ▼
    ┌── get_anchors_by_vector_similarity() ──┐
    │   Encode "System Design" → 768-dim     │
    │   Cosine search the vector index        │
    │   Result: ["Software Design" (0.95),    │
    │            "Clean Architecture" (0.82)] │
    └────────────┬───────────────────────────┘
                 │ HIT
                 ▼
    ┌── execute_spreading_activation_hop() ──┐
    │   BFS from "Software Design" (3 hops)  │
    │   BFS from "Clean Architecture" (3 hops)│
    │   Returns distance + degree for each    │
    └─────────────────────────────────────────┘
```
