# Module 12: Retrieval Engine — The Brain

## File Covered
`src/graph_cortex/core/retrieval/engine.py`

---

## What the Retrieval Engine Does

The `RetrievalEngine` is the **cognitive core** of GraphCortex. When the AI needs to recall information, this engine:

1. **Finds anchor nodes** using dual triggers (lexical string match → semantic vector fallback)
2. **Fans outward** from anchors using BFS traversal (Spreading Activation)
3. **Calculates energy decay** for every discovered node (Lateral Inhibition)
4. **Deduplicates** overlapping networks when multiple anchors activate
5. **Returns** a clean, filtered knowledge sub-graph

---

## Full Code with Line-by-Line Explanation

### Imports

```python
from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.infrastructure.db.queries.retrieval_queries import get_anchor_nodes_by_name, execute_spreading_activation_hop, get_anchors_by_vector_similarity
from graph_cortex.core.retrieval.inhibition import apply_lateral_inhibition
from graph_cortex.config.logger import get_retrieval_logger
from sentence_transformers import SentenceTransformer
```

| Import | Layer | Purpose |
|---|---|---|
| `get_session` | Infrastructure | Neo4j session factory |
| `get_anchor_nodes_by_name` | Infrastructure | Lexical Cypher query |
| `execute_spreading_activation_hop` | Infrastructure | BFS Cypher query |
| `get_anchors_by_vector_similarity` | Infrastructure | Vector search Cypher query |
| `apply_lateral_inhibition` | Core | Energy decay math |
| `get_retrieval_logger` | Config | Timestamped log writer |
| `SentenceTransformer` | External | Embedding model for vector fallback |

### Class Initialization

```python
class RetrievalEngine:
    """
    Orchestrates the Spreading Activation Retrieval process.
    Leverages Lexical/Semantic triggers to find anchors, and transverses outwards.
    """
    def __init__(self, cutoff_threshold=0.2, max_depth=3):
        self.cutoff_threshold = cutoff_threshold
        self.max_depth = max_depth
        self.semantic_model = None  # Lazy load SentenceTransformer here when needed
        self.logger = get_retrieval_logger()
```

| Attribute | Default | Purpose |
|---|---|---|
| `cutoff_threshold` | `0.2` | Minimum activation energy to keep a node (passed to Lateral Inhibition) |
| `max_depth` | `3` | Maximum BFS hop depth for Spreading Activation |
| `semantic_model` | `None` | Lazy-loaded embedding model (only loaded when lexical search fails) |
| `logger` | Logger instance | Writes timestamped events to `/Logs/retrieval_TIMESTAMP.log` |

---

### The `retrieve()` Method — Step by Step

#### Step 1A: Lexical Trigger

```python
    def retrieve(self, query_terms: list):
        # Step 1A: Lexical Trigger
        with get_session() as session:
            anchors = get_anchor_nodes_by_name(session, query_terms)
```

First attempt: Try to find nodes whose names contain the query string. If the user searches for `["Clean Architecture"]`, this will find the Entity directly.

**Result:** A list of anchor dicts, or an empty list if nothing matched.

#### Step 1B: Semantic Vector Fallback

```python
            # Step 1B: Semantic Vector Fallback
            if not anchors:
                self.logger.info(f"Lexical Miss for '{query_terms}'. Initiating Semantic Vector Fallback.")
                print(f"\n[!] Lexical miss for '{query_terms}'. Activating Semantic Vector Fallback...")
```

**The fallback trigger.** If lexical search found nothing (user searched `["System Design"]` but no node has that exact name), we switch to semantic search.

The event is both:
- **Logged** to the `/Logs` file for post-mortem analysis
- **Printed** to stdout for immediate feedback

```python
                if not self.semantic_model:
                    self.semantic_model = SentenceTransformer('BAAI/bge-base-en-v1.5', device='mps')
```
**Lazy loading.** The model is only loaded when actually needed (lexical miss). If lexical search always succeeds, the model never loads — saving 2-3 seconds of startup time and ~500MB of RAM.

`device='mps'` routes computation through Apple Silicon's Metal Performance Shaders GPU.

```python
                vector = self.semantic_model.encode(query_terms[0]).tolist()
                anchors = get_anchors_by_vector_similarity(session, vector, limit=2)
```
1. Encode the first query term into a 768-dimensional vector.
2. Pass it to Neo4j's native vector index for cosine similarity search.
3. Returns up to 2 anchors that exceed the 0.65 similarity threshold.

```python
                if not anchors:
                    self.logger.warning(f"Semantic Fallback Miss for '{query_terms}'. No anchors found.")
                    return {"status": "Miss", "anchors": [], "network": [], "inhibited_hubs": []}
                else:
                    self.logger.info(f"Semantic Fallback Success! Found semantic anchors: {anchors}")
            else:
                self.logger.info(f"Lexical Hit for '{query_terms}'. Found exact anchors: {anchors}")
```

**Three possible outcomes:**
1. **Lexical Hit** → Anchors found by string matching → Continue
2. **Semantic Hit** → Anchors found by vector similarity → Continue  
3. **Total Miss** → Neither method found anything → Return empty result immediately

#### Step 2: Spreading Activation from Anchors

```python
            # Step 2: Spreading Activation from Anchors
            activated_network = []
            dropped = []
            
            for anchor in anchors:
                # Add the anchor itself to the network with maximum energy
                activated_network.append({
                    "node_id": anchor["node_id"],
                    "name": anchor["name"],
                    "type": anchor["type"],
                    "distance": 0,
                    "degree": 1,
                    "activation_energy": 1.0  # Max energy for exact match anchor
                })
```
**The anchor gets maximum energy (1.0).** It's distance 0 (it IS the starting point) and degree 1 (we don't penalise the anchor itself for being connected).

```python
                # Traverse outwards (Fan out) up to depth limit
                traversed = execute_spreading_activation_hop(session, anchor["node_id"], self.max_depth)
```
**BFS explosion.** From the anchor, find all nodes within 3 hops. This will return dozens to hundreds of nodes, depending on graph density.

#### Step 3: Lateral Inhibition (Energy Decay)

```python
                # Step 3: Apply Lateral Inhibition (Energy Decay)
                filtered, hubs = apply_lateral_inhibition(
                    traversed, 
                    cutoff_threshold=self.cutoff_threshold
                )
                
                activated_network.extend(filtered)
                dropped.extend(hubs)
```
Pass the raw traversed nodes through the energy decay formula. Only nodes with `AE >= 0.2` survive. Hubs are logged as dropped.

#### Step 4: Network Deduplication

```python
            # Deduplicate by node_id, keeping the highest activation energy
            unique_network_dict = {}
            for node in activated_network:
                n_id = node["node_id"]
                if n_id not in unique_network_dict or node["activation_energy"] > unique_network_dict[n_id]["activation_energy"]:
                    unique_network_dict[n_id] = node
```

**Why deduplication is necessary:**  
When multiple anchors activate (e.g., both "Software Design" and "Clean Architecture"), their BFS traversals overlap. The same node might appear in both networks. We keep the instance with the **highest activation energy** — the one with the strongest relevance signal.

Example:
```
From "Software Design" BFS: {"name": "Event_001", "AE": 0.33}
From "Clean Architecture" BFS: {"name": "Event_001", "AE": 0.36}

→ Keep the one with AE = 0.36
```

#### Return the Final Result

```python
            return {
                "status": "Hit", 
                "anchors": [a["name"] for a in anchors],
                "network": list(unique_network_dict.values()),
                "inhibited_hubs": list(set(dropped))
            }
```

| Field | Type | Content |
|---|---|---|
| `status` | `"Hit"` or `"Miss"` | Whether any anchors were found |
| `anchors` | `["Software Design", "Clean Architecture"]` | Names of the anchor nodes that initiated activation |
| `network` | List of node dicts | The full activated, filtered, deduplicated knowledge sub-graph |
| `inhibited_hubs` | `["User", "Technology"]` | Names of nodes that were suppressed by Lateral Inhibition |

---

## The Complete Retrieval Pipeline

```
User: "System Design"
         │
         ▼
┌─ STEP 1A: LEXICAL TRIGGER ─────────────────────┐
│ Query: MATCH (n) WHERE n.name CONTAINS          │
│        "System Design"                          │
│ Result: [] (MISS — no exact match)              │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─ STEP 1B: SEMANTIC VECTOR FALLBACK ─────────────┐
│ Encode "System Design" → 768-dim vector (MPS)   │
│ Query Neo4j vector index (cosine search)         │
│ Result: ["Software Design" (0.95),               │
│          "Clean Architecture" (0.82)]            │
└──────────────────────┬──────────────────────────┘
                       │
         ┌─────────────┼──────────────┐
         │                            │
         ▼                            ▼
┌─ STEP 2: BFS FROM ──┐  ┌─ STEP 2: BFS FROM ──────┐
│ "Software Design"   │  │ "Clean Architecture"     │
│ Depth: 3 hops       │  │ Depth: 3 hops            │
│ Discovers: 15 nodes │  │ Discovers: 18 nodes      │
└─────────┬───────────┘  └──────────┬────────────────┘
          │                         │
          ▼                         ▼
┌─ STEP 3: LATERAL INHIBITION ─────────────────────┐
│ For each discovered node:                         │
│   AE = 1.0 / (dist_factor × degree_factor)       │
│   Keep if AE >= 0.2, drop otherwise              │
│                                                   │
│ Kept: 12 nodes    Dropped: 21 hubs               │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌─ STEP 4: DEDUPLICATE ────────────────────────────┐
│ Merge overlapping networks                        │
│ Keep highest AE for each unique node_id           │
│                                                   │
│ Final network: 10 unique nodes                    │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
              RETURN TO CALLER
```
