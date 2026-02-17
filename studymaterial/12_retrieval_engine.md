# Module 12: Retrieval Engine — The Brain

## File Covered
`src/graph_cortex/core/retrieval/engine.py`

---

## What the Retrieval Engine Does

The `RetrievalEngine` is the **cognitive core** of GraphCortex. When the AI needs to recall information, this engine:

1. **Finds anchor nodes** using a parallel **Hybrid Search** (Concurrent BM25 Fulltext Lexical + Dense Semantic Vector match)
2. **Deduplicates** the starting anchors.
3. **Fans outward** from anchors using BFS traversal (Spreading Activation)
4. **Calculates energy decay** for every discovered node (Lateral Inhibition)
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

#### Step 1: Hybrid Trigger (Parallel Search)

The engine pulls the raw query and immediately sanitizes it to support Lucene syntax parsing for BM25 matching.

```python
    def retrieve(self, query_terms: list):
        import re
        search_query = query_terms[0] if query_terms else ""
        
        # Strip punctuation to prevent Neo4j Lucene syntax errors during BM25 parsing
        bm25_safe_query = re.sub(r'[^A-Za-z0-9\s]', '', search_query).strip()
        
        with get_session() as session:
            # 1A: Fulltext BM25 Search
            bm25_anchors = get_anchors_by_fulltext(session, bm25_safe_query)
            
            # 1B: Dense Vector Semantic Search
            vector = encode_embedding(search_query)
            semantic_anchors = get_anchors_by_vector_similarity(session, vector)
```

The system executes BOTH searches simultaneously:
1. **BM25 Lexical Node Match**: High-precision detection of rigid keywords (like vault codes or chemistry elements) without semantic distraction.
2. **Embedding Vector Cosine Search**: Broad abstraction clustering. Finding "Software Design" when the user asks about "System Architecture".

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
┌─ STEP 1A: BM25 FULLTEXT LEXICAL SEARCH ─────────┐
│ Clean "System Design" (strip punctuation)       │
│ Query Neo4j Lucene Fulltext index               │
│ Result: [] (MISS — no exact match)              │
└──────────────────────┬──────────────────────────┘
                       │ Concurrent Execution
┌─ STEP 1B: DENSE VECTOR SEMANTIC SEARCH ─────────┐
│ Encode "System Design" → 768-dim vector         │
│ Query Neo4j vector index (cosine search)        │
│ Result: ["Software Design" (0.95),              │
│          "Clean Architecture" (0.82)]           │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─ STEP 1C: ANCHOR DEDUPLICATION ─────────────────┐
│ Merge the BM25 and Semantic Anchor sets         │
│ Keep unique nodes by node_id                    │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┴─────────────┐
          │                          │
          ▼                          ▼
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
