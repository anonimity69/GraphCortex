# Module 08: Memory Manager Orchestrator

## File Covered
`src/graph_cortex/core/memory/manager.py`

---

## What the Memory Manager Does

The `MemoryManager` is the **traffic cop** of the entire memory system. It provides a clean, high-level API that the interface layer calls. Internally, it delegates to the three memory sub-systems in the correct sequence. No external code needs to know about Working, Episodic, or Semantic memory individually.

---

## Full Code with Line-by-Line Explanation

```python
from graph_cortex.core.memory.working import WorkingMemory
from graph_cortex.core.memory.episodic import EpisodicMemory
from graph_cortex.core.memory.semantic import SemanticMemory
from graph_cortex.infrastructure.storage.sharding import sharder
from typing import List, Dict
```
Imports all three memory sub-systems plus the property sharder. Notice the imports follow Clean Architecture — core imports core, but also reaches into infrastructure for the sharder (this is the one pragmatic exception where the `manager` uses a thin infrastructure utility).

```python
class MemoryManager:
    """
    Orchestrates the Multi-Layered Memory Framework (MLMF).
    Handles the pipeline from raw interaction -> event summarization -> semantic extraction.
    """
    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
```
**Composition over Inheritance.** The MemoryManager doesn't inherit from any memory class — it *contains* instances of all three. This is the **Facade Pattern** — it hides complexity behind a simple interface.

---

### Method 1: `process_turn()` — Real-Time Ingestion

```python
    def process_turn(self, session_id: str, user_input: str, agent_response: str):
        self.working.add_interaction(session_id)
        self.working.add_message(session_id, role="user", content=user_input)
        self.working.add_message(session_id, role="agent", content=agent_response)
        return True
```

**What happens in sequence:**

| Step | Method Called | What It Creates |
|---|---|---|
| 1 | `add_interaction(session_id)` | Creates/finds the `Interaction` node for this session |
| 2 | `add_message(..., role="user", ...)` | Creates a `Message` node, links it via `[:CONTAINS]` and `[:NEXT]` |
| 3 | `add_message(..., role="agent", ...)` | Creates another `Message`, chains it via `[:NEXT]` to the user message |

**Result in Neo4j:**
```
(Interaction) --[:CONTAINS]--> (Message: user) --[:NEXT]--> (Message: agent)
                └──[:CONTAINS]─────────────────────────────────────┘
```

**Important:** `process_turn()` only touches **Working Memory**. No summarisation, no knowledge extraction. It's designed to be called in real-time during a conversation.

---

### Method 2: `consolidate_episode()` — Knowledge Extraction Pipeline

```python
    def consolidate_episode(self, session_id: str, generated_summary: str, extracted_entities: List[Dict]):
```
**Parameters:**
- `session_id` — Which conversation to consolidate
- `generated_summary` — A human-readable summary (typically LLM-generated)
- `extracted_entities` — A list of structured facts extracted from the conversation

**Example `extracted_entities`:**
```python
[
    {"entity": "Clean Architecture", "concept": "Software Design", "relation": "IS_A_PATTERN_OF"},
    {"entity": "Neo4j Driver", "concept": "Infrastructure", "relation": "BELONGS_TO_LAYER"}
]
```

```python
        # Property Shard the potentially heavy summary
        stored_summary_ref = sharder.store(f"ep_{session_id}", generated_summary)
```
**Step 1: Property Sharding.** The summary text can be very long. Rather than storing heavy text directly on the graph node (which slows down traversal), we pass it through the sharder. Currently in "local" mode, the sharder just returns the string unchanged. In production with `mode="s3"`, it would upload the text to S3 and return a lightweight URI like `s3://ns-dmg-shard/ep_session_abc`.

```python
        # Create Episodic Event
        event_id = self.episodic.create_event(session_id, stored_summary_ref)
```
**Step 2: Episodic Memory.** Creates the Event node with the summary, links it to the Interaction via `[:SUMMARIZES]`, and chains it to the previous event via `[:FOLLOWS]`.

```python
        # Extract into Semantic Memory layer
        for item in extracted_entities:
            self.semantic.add_entity(item["entity"])
            self.semantic.add_entity(item["concept"])
            self.semantic.extract_from_event(
                event_id=event_id,
                entity_name=item["entity"],
                concept_name=item["concept"],
                relationship_type=item.get("relation", "RELATED_TO")
            )
```
**Step 3: Semantic Memory.** For each extracted fact:
1. `add_entity(item["entity"])` — Ensures the Entity node exists and has a 768-dim embedding.
2. `add_entity(item["concept"])` — Same for the Concept node.
3. `extract_from_event(...)` — Links both to the source Event and creates the domain relationship between them.

**Why `add_entity()` before `extract_from_event()`?**  
`extract_from_event()` uses `MERGE`, which also creates nodes. But calling `add_entity()` first ensures the embedding is set even if `extract_from_event()` is called with different parameters later. It's a belt-and-suspenders approach.

```python
        return event_id
```
Returns the Event ID so the caller can reference it.

---

## The Complete Pipeline Visualised

```
process_turn()                          consolidate_episode()
═══════════════                         ═════════════════════
                                        
User says: "How does                    LLM generates:
clean architecture..."                  Summary: "User asked about
                │                       Clean Architecture..."
                ▼                               │
        ┌───────────────┐                       ▼
        │  WORKING      │               ┌───────────────┐
        │  MEMORY       │               │  PROPERTY     │
        │               │               │  SHARDER      │
        │ Interaction   │               │ (offload text)│
        │    └─ Msg 1   │               └───────┬───────┘
        │       └─ Msg 2│                       │
        └───────────────┘                       ▼
                                        ┌───────────────┐
                                        │  EPISODIC     │
                                        │  MEMORY       │
                                        │               │
                                        │ Event ─FOLLOWS─> prev
                                        │   └─SUMMARIZES─> Interaction
                                        └───────┬───────┘
                                                │
                                                ▼
                                        ┌───────────────┐
                                        │  SEMANTIC     │
                                        │  MEMORY       │
                                        │               │
                                        │ Entity ──REL──> Concept
                                        │   └─EXTRACTED_FROM─> Event
                                        └───────────────┘
```

---

## Common Client Questions

**Q: "Why are these two separate methods instead of one?"**  
A: In a real-time chat application, `process_turn()` is called on every single message exchange (milliseconds matter). `consolidate_episode()` is called at the end of a conversation or periodically — it's more expensive because it runs the embedding model, generates summaries, and creates semantic links. Separating them lets you handle real-time ingestion at full speed without blocking on ML inference.

**Q: "Where does the summary come from?"**  
A: The `generated_summary` parameter is expected to come from an LLM. In a production pipeline, you'd call something like `GPT-4o: Summarize this conversation in one sentence` and pass the result here.
