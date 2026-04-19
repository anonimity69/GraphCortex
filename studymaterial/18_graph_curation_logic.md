# Module 18: Graph Curation Logic (The Muscles)

## File Covered
- `src/graph_cortex/core/memory/curation.py`

---

## The Philosophy of Curation

In a standard Knowledge Graph, data grows indefinitely. Without curation, the graph eventually suffers from "Information Overload," where every concept is connected to everything else, rendering **Spreading Activation** useless.

The `MemoryCuration` class provides the "muscles" that allow the RL Librarian to physically prune and shape the graph to maintain high logic density.

---

## Global Soft-Deletion Architecture

GraphCortex does not use `DETACH DELETE` for curation. Instead, we use a **Global Soft-Deletion** pattern.

### Why Soft-Delete?
1.  **Chronological Integrity**: Even if a node is no longer useful for retrieval, it is still part of the interaction history. Removing it physically would break the `[:FOLLOWS]` chains in Episodic Memory.
2.  **Restore Capability**: If the RL Librarian makes a mistake and deletes a critical node, the system can "re-learn" and restore it by simply flipping a boolean flag.

```python
def set_node_active_status(self, node_id: str, status: bool = False):
    query = """
    MATCH (n) WHERE elementId(n) = $node_id
    SET n.is_active = $status
    RETURN n.name AS name, n.is_active AS is_active
    """
```

Nodes with `is_active = False` are ignored by the Spreading Activation algorithm, effectively removing them from the AI's "consciousness" while keeping them in the database for historical auditing.

---

## Idempotent Knowledge Merging

The `merge_node` function allows the Librarian to inject new facts or concepts into the graph.

```python
def merge_node(self, label: str, name: str, properties: dict = None):
    # Ensure we track that this was an RL-optimized node
    properties['curated_by'] = 'RL_Librarian'
    
    query = f"MERGE (n:{label} {{name: $name}}) SET n += $props RETURN n"
```

- **`MERGE`**: Matches existing nodes by name to prevent duplicates.
- **`SET n += $props`**: Updates the properties without wiping existing ones.
- **Provenance Tracking**: We add `curated_by: 'RL_Librarian'` to every node touched by RL, allowing us to audit how much of the graph is human-generated vs. agent-optimized.

---

## Summary of Operations

| Method | Operation Type | Effect |
| :--- | :--- | :--- |
| `merge_node` | Write / Update | Creates a new entity or updates an existing one identified by name. |
| `update_node` | Update | Modifies a specific node using its internal Neo4j `elementId`. |
| `set_node_active_status` | Status Flip | Toggles the `is_active` flag to enable/disable a node in retrieval. |

By separating these "muscles" into a dedicated service, the **Intelligence Layer** remains clean and focused on high-level strategy rather than raw database syntax.
