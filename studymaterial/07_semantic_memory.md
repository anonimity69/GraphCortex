# Module 07: Semantic Memory & Embeddings

## File Covered
`src/graph_cortex/core/memory/semantic.py`

---

## What Semantic Memory Does

Semantic Memory extracts **structured facts** from episodic events. While Episodic Memory captures "what happened," Semantic Memory captures "what we now know." It creates `Entity` nodes (specific things) and `Concept` nodes (abstract ideas), links them with domain-specific relationships, and embeds them as 768-dimensional vectors for semantic search.

**Graph structure it creates:**
```
(Entity: "Clean Architecture") ──[:IS_A_PATTERN_OF]──> (Concept: "Software Design")
    │                                                      │
    └── [:EXTRACTED_FROM] → (Event_001)              └── [:EXTRACTED_FROM] → (Event_001)
```

---

## Full Code with Line-by-Line Explanation

```python
from typing import List, Dict
from graph_cortex.infrastructure.db.neo4j_connection import get_session
```

```python
class SemanticMemory:
    """
    Entity-level abstractions.
    Maps out global knowledge elements derived from specific episodic events.
    """
    def __init__(self):
        self.semantic_model = None
```
**`self.semantic_model = None`** — This is the lazy-loading slot for the SentenceTransformer model. We don't load the model here because:
1. It takes 2-3 seconds and ~500MB of RAM.
2. Some operations might not need embeddings.
3. We only want to load it once and cache it.

---

### The Embedding Engine: `_get_embedding()`

```python
    def _get_embedding(self, text: str) -> List[float]:
        """Lazy loads SentenceTransformer using Apple Silicon MPS and returns a 768-dimensional vector."""
        if not self.semantic_model:
            from sentence_transformers import SentenceTransformer
            self.semantic_model = SentenceTransformer('BAAI/bge-base-en-v1.5', device='mps')
        return self.semantic_model.encode(text).tolist()
```

**Line-by-line:**

| Line | Explanation |
|---|---|
| `if not self.semantic_model:` | **Lazy loading guard.** Only loads the model on the very first call. All subsequent calls skip straight to `encode()`. |
| `from sentence_transformers import SentenceTransformer` | **Deferred import.** The `import` is inside the function, not at the top of the file. This means if the `sentence-transformers` package isn't installed, the rest of the file still imports fine — it only fails when you actually try to embed something. |
| `SentenceTransformer('BAAI/bge-base-en-v1.5', device='mps')` | **Model loading.** Downloads (first time) and loads the BGE-base model with ~109M parameters. `device='mps'` routes all tensor operations through Apple Silicon's Metal Performance Shaders GPU instead of the CPU. |
| `.encode(text)` | Converts the input string into a 768-dimensional numpy array. Internally, the model tokenises the text, passes it through 12 transformer layers, and mean-pools the output. |
| `.tolist()` | Converts the numpy array to a plain Python list of floats, which Neo4j can store natively. |

**What is an embedding?**  
An embedding is a mathematical representation of meaning. The model converts text like `"Clean Architecture"` into a list of 768 numbers: `[0.0312, -0.0891, 0.1245, ...]`. Texts with similar meanings produce similar number patterns. You can measure this similarity using cosine distance.

Example:
```
"Clean Architecture" → [0.03, -0.09, 0.12, ...]
"Software Design"    → [0.04, -0.08, 0.11, ...]   ← Very similar! (cosine ≈ 0.95)
"Pizza Recipe"       → [-0.21, 0.45, -0.33, ...]  ← Very different! (cosine ≈ 0.12)
```

---

### Method 1: `add_entity()`

```python
    def add_entity(self, name: str, node_type: str = "Entity", attributes: Dict = None):
        """Creates or updates a general semantic entity, embedding it as a vector."""
        if attributes is None:
            attributes = {}
```
**Mutable default argument guard.** In Python, `def f(x={})` is a famous bug — the empty dict is shared across all calls. Setting it to `None` and creating a new dict inside the function prevents this.

```python
        embedding = self._get_embedding(name)
```
**Immediate embedding.** The moment an entity is created, it gets vectorised. There's no "unembedded" state — every Entity in the database always has an `embedding` property.

```python
        query = f"MERGE (e:{node_type} {{name: $name}}) "
```
**Dynamic label.** The `node_type` parameter defaults to `"Entity"` but can be set to `"Concept"` or any other label. The f-string is used here because **Neo4j parameters cannot be used for labels** — only for property values. This is a Cypher language limitation.

**Security note:** Since `node_type` comes from internal code (not user input), this is safe. If it were user-facing input, you'd need to whitelist allowed labels.

```python
        set_statements = ["e.embedding = $embedding"]
        for k in attributes.keys():
            set_statements.append(f"e.{k} = ${k}")
            
        query += f"SET {', '.join(set_statements)} "
        query += "RETURN e.name AS name"
```
**Dynamic SET construction.** Builds a SET clause like:
```cypher
SET e.embedding = $embedding, e.description = $description, e.category = $category
```
This allows arbitrary additional attributes without modifying the Cypher template.

```python
        with get_session() as session:
            session.run(query, name=name, embedding=embedding, **attributes)
        return name
```
**`**attributes`** unpacks the dictionary as keyword arguments, passing them all to Neo4j as parameters.

---

### Method 2: `extract_from_event()` — The Knowledge Extraction Pipeline

```python
    def extract_from_event(self, event_id: str, entity_name: str, concept_name: str, relationship_type: str = "RELATED_TO"):
        """
        Extracts structured semantic knowledge from an event and calculates vector embeddings.
        """
        rel_type = relationship_type.upper().replace(" ", "_")
```
**Relationship sanitisation.** Neo4j relationship types must be uppercase with underscores by convention. `"is a pattern of"` becomes `"IS_A_PATTERN_OF"`.

```python
        entity_vector = self._get_embedding(entity_name)
        concept_vector = self._get_embedding(concept_name)
```
**Both get embedded.** The entity ("Clean Architecture") and the concept ("Software Design") are independently converted into 768-dim vectors.

```python
        query = f"""
        MATCH (ev:Event {{event_id: $event_id}})
        MERGE (e:Entity {{name: $entity_name}})
        SET e.embedding = $entity_vector
        
        MERGE (c:Concept {{name: $concept_name}})
        SET c.embedding = $concept_vector
        
        MERGE (e)-[:EXTRACTED_FROM]->(ev)
        MERGE (c)-[:EXTRACTED_FROM]->(ev)
        MERGE (e)-[:{rel_type}]->(c)
        """
```

**This single Cypher query does 5 things atomically:**

| Step | Cypher | What It Does |
|---|---|---|
| 1 | `MATCH (ev:Event {event_id: ...})` | Find the source event |
| 2 | `MERGE (e:Entity {name: ...})` | Find or create the Entity node |
| 3 | `SET e.embedding = ...` | Store/update the 768-dim vector |
| 4 | `MERGE (e)-[:EXTRACTED_FROM]->(ev)` | Link entity to its source event (provenance) |
| 5 | `MERGE (e)-[:IS_A_PATTERN_OF]->(c)` | Create the semantic relationship |

**Why `MERGE` everywhere?**  
`MERGE` is idempotent. If you call `extract_from_event()` twice with the same entity name, it won't create duplicates — it'll find the existing node and just update the embedding. This makes the system resilient to repeated processing.

**Why `f-string` for the relationship type?**  
Same as labels — Cypher doesn't allow parameterised relationship types. `MERGE (e)-[:$type]->(c)` is invalid Cypher. So we use an f-string with the sanitised `rel_type`.

---

## The Knowledge Graph After Extraction

```
                    (Event_001: "User asked about Clean Architecture...")
                   /              |                  \
          [:EXTRACTED_FROM]  [:EXTRACTED_FROM]    [:EXTRACTED_FROM]
                /                 |                    \
(Entity: "Clean Architecture")  (Concept: "Software Design")  (Entity: "Neo4j Driver")
         |                                                          |
         └── [:IS_A_PATTERN_OF] → (Concept: "Software Design")     |
                                                                    └── [:BELONGS_TO_LAYER] → (Concept: "Infrastructure")
```

This creates a rich **knowledge graph** where:
- Facts are linked to their sources (provenance tracking).
- Entities are connected to abstract concepts.
- The AI can traverse from any node to discover related knowledge.
