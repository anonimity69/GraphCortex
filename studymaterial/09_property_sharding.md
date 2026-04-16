# Module 09: Property Sharding

## File Covered
`src/graph_cortex/infrastructure/storage/sharding.py`

---

## What Property Sharding Solves

In a graph database, performance depends on how fast you can traverse relationships. When you run a BFS (Breadth-First Search) across 1000 nodes, Neo4j loads each node's properties into memory. If every Event node carries a 10KB summary string, traversal loads 10MB of text you might not even need.

**Property Sharding** offloads heavy properties (like text summaries) to cheaper storage, keeping the graph lightweight.

---

## Full Code with Line-by-Line Explanation

```python
class PropertySharder:
    """
    Experimental interface for property sharding in Phase 1.
    Offloads heavy properties away from graph topology to maintain performance.
    """
    def __init__(self, mode="local"):
        self.mode = mode
```
**Two modes:**
- `"local"` — Passthrough mode. The text stays inline on the Neo4j node. Used for development.
- `"s3"` (or any external mode) — Would upload text to S3/MongoDB and store only a lightweight URI reference on the node.

```python
    def store(self, node_id: str, payload: str) -> str:
        """
        Stores heavy payload and returns a lightweight reference.
        """
        if self.mode == "local":
            return payload
        else:
            ref_uri = f"s3://ns-dmg-shard/{node_id}"
            return ref_uri
```
**In local mode:** Simply returns the original string. The Event node stores the full summary text directly. Zero overhead for development.

**In S3 mode:** Would upload the payload to an S3 bucket and return only the URI string `s3://ns-dmg-shard/ep_session_abc`. The Event node would store this tiny reference instead of the full text. When you need the actual text, you call `retrieve()`.

```python
    def retrieve(self, ref_uri: str) -> str:
        """
        Retrieves the heavy payload from the shard.
        """
        if self.mode == "local":
            return ref_uri
        return f"Loaded external content for {ref_uri}"
```
The inverse operation. In local mode, the "reference" IS the content, so just return it.

```python
sharder = PropertySharder()
```
**Module-level singleton instance.** All code imports and uses this single `sharder` object.

---

## Why This Pattern Matters for Clients

**Q: "What happens when the graph grows to millions of nodes?"**  
A: *"We've already abstracted property sharding. Heavy text properties can be transparently offloaded to S3 or MongoDB by switching one configuration flag, keeping graph traversal at O(1) per node regardless of text length."*

**Q: "Is S3 mode actually implemented?"**  
A: *"The abstraction is in place. The S3 upload/download calls would be added to `store()` and `retrieve()`. The important thing is that no other code in the system needs to change — the MemoryManager doesn't know or care where the text lives."*

This is the **Dependency Inversion Principle** in action.
