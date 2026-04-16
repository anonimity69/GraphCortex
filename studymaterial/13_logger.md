# Module 13: Logger Configuration

## File Covered
`src/graph_cortex/config/logger.py`

---

## What the Logger Does

Creates a dedicated, timestamped log file every time the `RetrievalEngine` runs. This provides a permanent audit trail of:
- When the Lexical trigger hit vs. missed
- When the Semantic Vector Fallback was activated
- What anchors were found and their similarity scores

---

## Full Code with Line-by-Line Explanation

```python
import os
import logging
from datetime import datetime
```
- `os` — File path construction and directory creation.
- `logging` — Python's built-in structured logging framework.
- `datetime` — Timestamp generation for unique log filenames.

```python
# Build absolute path to the Logs directory at the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
LOGS_DIR = os.path.join(PROJECT_ROOT, "Logs")
```

**Path resolution explained:**
```
__file__              = .../src/graph_cortex/config/logger.py
os.path.dirname(...)  = .../src/graph_cortex/config/
"../../../"           = .../src/graph_cortex/config/ → config/ → graph_cortex/ → src/ → PROJECT ROOT
os.path.abspath(...)  = /Users/.../Developer/GraphCortex/
```

`LOGS_DIR` becomes `/Users/.../Developer/GraphCortex/Logs/`.

```python
# Ensure the Logs directory physically exists early
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
```
**Module-level execution.** This runs when the file is first imported. If the `Logs/` directory doesn't exist, it's created automatically. `os.makedirs()` creates any missing intermediate directories too.

---

### The `get_retrieval_logger()` Function

```python
def get_retrieval_logger():
    """
    Configures and returns a dedicated logger for Retrieval operations.
    Maintains a physical trail of Lexical vs Semantic Fallback triggers.
    """
    logger = logging.getLogger("RetrievalEngine")
```
**Named logger.** `logging.getLogger("RetrievalEngine")` returns a logger specific to the retrieval engine. Python's logging module uses a singleton pattern — calling `getLogger("RetrievalEngine")` anywhere in the codebase always returns the same logger instance.

```python
    # Only configure if it doesn't already have handlers to prevent duplicate lines
    if not logger.handlers:
        logger.setLevel(logging.INFO)
```
**Idempotency guard.** If `get_retrieval_logger()` is called multiple times (e.g., creating multiple `RetrievalEngine` instances), we don't want to add duplicate file handlers. The `if not logger.handlers` check ensures configuration happens only once.

`logging.INFO` means it captures `INFO`, `WARNING`, `ERROR`, and `CRITICAL` messages. It ignores `DEBUG`.

```python
        # Create a timestamped log file specific to this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(LOGS_DIR, f"retrieval_{timestamp}.log")
```
Each run of the application gets its own log file. Example: `retrieval_20260416_184741.log`. This means you can compare logs from different runs side by side.

```python
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
```
**FileHandler** writes log messages to the specified file. Each handler can have its own level — here it matches the logger's level.

```python
        # Structural logging format for easy analysis
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
```
**Log format:**
```
[2026-04-16 18:47:41] [INFO] - Lexical Miss for '['System Design']'. Initiating Semantic Vector Fallback.
[2026-04-16 18:47:43] [INFO] - Semantic Fallback Success! Found semantic anchors: [...]
```

| Token | Example | Meaning |
|---|---|---|
| `%(asctime)s` | `2026-04-16 18:47:41` | Timestamp when the event occurred |
| `%(levelname)s` | `INFO` | Severity level |
| `%(message)s` | `Lexical Miss for...` | The actual log message |

```python
        logger.addHandler(file_handler)
        
    return logger
```
Attaches the handler to the logger and returns it. All subsequent `logger.info(...)` calls will write to this file.

---

## Example Log Output

```
[2026-04-16 18:47:41] [INFO] - Lexical Miss for '['System Design']'. Initiating Semantic Vector Fallback.
[2026-04-16 18:47:43] [INFO] - Semantic Fallback Success! Found semantic anchors: [{'node_id': '4:9797d7c4-584c-4079-aa81-e6823e69e5dc:7', 'name': 'Software Design', 'type': 'Entity', 'score': 0.9484214782714844}, {'node_id': '4:9797d7c4-584c-4079-aa81-e6823e69e5dc:6', 'name': 'Clean Architecture', 'type': 'Entity', 'score': 0.8223938941955566}]
```

This log tells you exactly:
1. **18:47:41** — Lexical search failed (no exact string match for "System Design")
2. **18:47:43** — 2 seconds later, the semantic fallback found 2 anchors with high cosine scores

The 2-second gap is the time taken to lazy-load the `bge-base-en-v1.5` model on MPS and compute the embedding.
