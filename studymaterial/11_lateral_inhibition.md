# Module 11: Lateral Inhibition — The Math

## File Covered
`src/graph_cortex/core/retrieval/inhibition.py`

---

## The Neuroscience Behind It

**Lateral Inhibition** is a real phenomenon in the human brain. When one neuron fires strongly, it suppresses the firing of its neighbours. This prevents the brain from being overwhelmed by noise and forces it to focus on the most relevant signals.

**The Hub Explosion Problem:**  
In a knowledge graph, some nodes are "hubs" — they connect to everything. For example, a node labelled `"User"` might be linked to every single interaction. If Spreading Activation reaches `"User"`, it would fan out to thousands of nodes, flooding the AI's context window with irrelevant garbage.

Lateral Inhibition mathematically suppresses these hubs.

---

## The Energy Decay Formula

```
AE = initial_energy / (((distance × distance_penalty) + 1) × ((degree × degree_penalty) + 1))
```

### What Each Variable Means

| Variable | Default | What It Controls |
|---|---|---|
| `initial_energy` | `1.0` | The starting energy of an anchor node (maximum = 1.0). |
| `distance` | varies | How many hops this node is from the anchor (returned by BFS query). |
| `distance_penalty` | `0.5` | How aggressively energy decays with distance. Higher = faster decay. |
| `degree` | varies | How many relationships this node has (returned by BFS query). |
| `degree_penalty` | `0.1` | How aggressively energy decays for hub nodes. Higher = harsher on hubs. |
| `cutoff_threshold` | `0.2` | Minimum energy required to survive. Below this = inhibited/dropped. |

### Why `+1` in the Formula?

Without `+1`, the formula would be:
```
AE = 1.0 / ((distance × 0.5) × (degree × 0.1))
```

Problem: If `distance = 0` (the anchor itself), the denominator becomes 0, causing a **division by zero**. Adding `+1` ensures the denominator is always at least 1.

For the anchor node itself (distance=0, degree=1):
```
AE = 1.0 / (((0 × 0.5) + 1) × ((1 × 0.1) + 1))
AE = 1.0 / (1 × 1.1)
AE = 0.909   (Near-maximum energy ✅)
```

---

## Full Code with Line-by-Line Explanation

```python
def apply_lateral_inhibition(traversed_nodes, initial_energy=1.0, degree_penalty=0.1, distance_penalty=0.5, cutoff_threshold=0.2):
    """
    Simulates lateral inhibition and the Fan Effect computationally.
    Calculates the Activation Energy (AE) for each node.
    AE = initial_energy / (((distance * distance_penalty) + 1) * ((degree * degree_penalty) + 1))
    Nodes whose AE falls below the cutoff_threshold are inhibited/dropped.
    """
```
**Pure function.** No database imports, no side effects, no state. Given the same input, it always produces the same output. This is a core principle of Clean Architecture — the math is testable without any infrastructure.

```python
    filtered_nodes = []
    dropped_hubs = []
```
Two output lists: nodes that survive the filter, and nodes that get inhibited.

```python
    for node_data in traversed_nodes:
        degree = node_data.get("degree", 1)
        distance = node_data.get("distance", 1)
```
**`.get("degree", 1)`** — Safe dictionary access with a default value. If a node somehow doesn't have a `degree` field, it defaults to 1 (no penalty).

```python
        # Calculate Activation Energy (Decay Formula)
        denominator = ((distance * distance_penalty) + 1) * ((degree * degree_penalty) + 1)
        activation_energy = initial_energy / denominator
```
The core math. Let's trace through multiple examples:

```python
        node_data["activation_energy"] = round(activation_energy, 4)
```
**Mutates the input dictionary** by adding an `activation_energy` field. Rounded to 4 decimal places for readability. This value gets passed back to the Retrieval Engine and included in the final output.

```python
        if activation_energy >= cutoff_threshold:
            filtered_nodes.append(node_data)
        else:
            dropped_hubs.append(node_data.get("name", "UnknownHub"))
```
The binary decision: survive or die. If `AE >= 0.2`, the node is relevant enough to keep. Otherwise, it's logged as an inhibited hub and dropped.

```python
    return filtered_nodes, dropped_hubs
```
Returns both lists so the caller can report what was kept and what was dropped.

---

## Worked Examples with Real Data

### Example 1: Close, Specific Node (SURVIVES ✅)
```
Node: "Software Design" (distance=2, degree=4)

denominator = ((2 × 0.5) + 1) × ((4 × 0.1) + 1)
            = (1 + 1) × (0.4 + 1)
            = 2 × 1.4
            = 2.8

AE = 1.0 / 2.8 = 0.3571

0.3571 >= 0.2? YES → SURVIVES ✅
```

### Example 2: Far, Specific Node (SURVIVES ✅)
```
Node: "Neo4j Driver" (distance=3, degree=2)

denominator = ((3 × 0.5) + 1) × ((2 × 0.1) + 1)
            = (1.5 + 1) × (0.2 + 1)
            = 2.5 × 1.2
            = 3.0

AE = 1.0 / 3.0 = 0.3333

0.3333 >= 0.2? YES → SURVIVES ✅
```

### Example 3: Close Hub Node (BORDERLINE ⚠️)
```
Node: "Project" (distance=1, degree=15)

denominator = ((1 × 0.5) + 1) × ((15 × 0.1) + 1)
            = (0.5 + 1) × (1.5 + 1)
            = 1.5 × 2.5
            = 3.75

AE = 1.0 / 3.75 = 0.2667

0.2667 >= 0.2? YES → BARELY SURVIVES ⚠️
```

### Example 4: Far Hub Node (INHIBITED ❌)
```
Node: "User" (distance=3, degree=50)

denominator = ((3 × 0.5) + 1) × ((50 × 0.1) + 1)
            = (1.5 + 1) × (5 + 1)
            = 2.5 × 6.0
            = 15.0

AE = 1.0 / 15.0 = 0.0667

0.0667 >= 0.2? NO → INHIBITED ❌
```

### Example 5: Distant Generic Concept (INHIBITED ❌)
```
Node: "Technology" (distance=4, degree=30)

denominator = ((4 × 0.5) + 1) × ((30 × 0.1) + 1)
            = (2 + 1) × (3 + 1)
            = 3.0 × 4.0
            = 12.0

AE = 1.0 / 12.0 = 0.0833

0.0833 >= 0.2? NO → INHIBITED ❌
```

---

## Visualising the Filter

```
                    ANCHOR: "Clean Architecture" (AE = 1.0) ✅
                   /                    \
         distance=2                   distance=2
              /                            \
"Software Design" (AE=0.36) ✅    "Event_001" (AE=0.33) ✅
              |                            |
         distance=3                   distance=3
              |                            |
"Neo4j Driver" (AE=0.33) ✅      "User" (degree=50, AE=0.07) ❌ INHIBITED
                                           |
                                      distance=4
                                           |
                                  "Technology" (AE=0.08) ❌ INHIBITED
```

The hub nodes (`"User"`, `"Technology"`) are automatically suppressed, keeping the AI's context window focused on relevant, specific knowledge.

---

## Tuning Guide

| If you want... | Adjust... |
|---|---|
| More aggressive hub suppression | Increase `degree_penalty` (e.g., 0.2) |
| Deeper traversal reach | Decrease `distance_penalty` (e.g., 0.3) |
| Keep more nodes | Decrease `cutoff_threshold` (e.g., 0.1) |
| Keep fewer nodes | Increase `cutoff_threshold` (e.g., 0.3) |
| More energy at the anchor | Increase `initial_energy` (e.g., 2.0) |
