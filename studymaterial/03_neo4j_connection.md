# Module 03: Neo4j Connection — The Singleton Pattern

## File Covered
`src/graph_cortex/infrastructure/db/neo4j_connection.py`

---

## Full Code with Line-by-Line Explanation

```python
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
```
- `os` — Access environment variables from the system.
- `GraphDatabase` — The official Neo4j Python driver's entry point for creating database connections.
- `load_dotenv` — Reads the `.env` file and injects its key-value pairs into `os.environ` so they behave like real system environment variables.

```python
load_dotenv()
```
**Critical:** This must be called at module import time (top-level), not inside a function. It reads `.env` and makes `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` available via `os.getenv()`.

---

### The Singleton Pattern

```python
class Neo4jConnection:
    _instance = None  # Class-level variable shared across ALL instances
```

**What is a Singleton?**  
A Singleton ensures only **one instance** of a class ever exists. No matter how many times you call `Neo4jConnection()`, you always get back the exact same object.

**Why do we need it here?**  
Creating a Neo4j driver is expensive — it establishes a TCP connection pool, negotiates the Bolt protocol version, and authenticates. If every memory layer (`WorkingMemory`, `EpisodicMemory`, `SemanticMemory`) each created their own driver, you'd have 3+ redundant connection pools fighting over sockets. The Singleton ensures one shared pool.

```python
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
```
**`__new__` vs `__init__`:**  
- `__new__` controls **object creation** (allocating memory).
- `__init__` controls **object initialization** (setting attributes).

By overriding `__new__`, we intercept the creation step. If `_instance` is `None` (first call), we create the object normally. On every subsequent call, we skip creation and return the existing instance.

```python
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            username = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "changeme123")
```
**Fallback defaults:** If the `.env` file is missing or a variable isn't set, these defaults kick in. The default password `changeme123` is intentionally weak to signal "you forgot to configure this."

```python
            try:
                cls._instance.driver = GraphDatabase.driver(uri, auth=(username, password))
            except Exception as e:
                print(f"Failed to connect to Neo4j: {e}")
                cls._instance.driver = None
```
**Error handling:** If Neo4j is offline, we don't crash the entire application. Instead, `driver` is set to `None`, and downstream code can check for this. The `GraphDatabase.driver()` call doesn't actually connect yet — it creates a lazy connection pool that connects on first use.

```python
        return cls._instance
```
**Always returns the same instance.** Whether it's the first call or the hundredth, `cls._instance` is the same object.

---

### Session Management

```python
# Global connection instance
db_connection = Neo4jConnection()
```
**Module-level instantiation.** When any file imports from `neo4j_connection`, this line executes, creating (or reusing) the Singleton. Every module that imports `get_session` shares the same underlying driver.

```python
def get_session():
    """Returns a Neo4j session"""
    driver = db_connection.get_driver()
    if driver:
        return driver.session()
    raise ConnectionError("Neo4j driver is not initialized.")
```
**What is a "session"?**  
A session is a lightweight, short-lived object that borrows a connection from the driver's pool, executes queries, and returns the connection when done. Sessions are designed to be used with Python's `with` statement:

```python
with get_session() as session:
    session.run("MATCH (n) RETURN n")
# Session automatically closes here, connection returns to pool
```

**Why `raise ConnectionError`?**  
If the driver is `None` (Neo4j is offline), we fail loudly rather than returning `None` and causing mysterious `NoneType has no attribute 'run'` errors deep in the call stack.

```python
def execute_read_query(query: str, **kwargs):
    """Executes a generic read transaction and returns a list of dictionaries."""
    with get_session() as session:
        result = session.run(query, **kwargs)
        return [record.data() for record in result]
```
**Utility function** for simple read-only queries. Converts Neo4j `Record` objects into plain Python dictionaries. The `**kwargs` allows passing Cypher parameters:

```python
execute_read_query("MATCH (n:Entity {name: $name}) RETURN n", name="Clean Architecture")
```

---

## How Other Files Use This

Every memory layer imports the same function:

```python
from graph_cortex.infrastructure.db.neo4j_connection import get_session

with get_session() as session:
    session.run(query, ...)
```

They all share the same Singleton driver → same connection pool → efficient resource usage.

---

## Common Client Questions

**Q: "What happens if Neo4j goes down mid-operation?"**  
A: The Neo4j Python driver has built-in retry logic and connection health checks. If a connection drops, the driver automatically tries to acquire a new one from the pool. For the current implementation, if the initial connection fails entirely, `driver` is `None` and all operations raise `ConnectionError`.

**Q: "Is this thread-safe?"**  
A: Yes. The Neo4j Python driver's connection pool is thread-safe by design. Multiple threads can call `get_session()` concurrently, and each gets its own session from the shared pool.

**Q: "Why not use a connection per request?"**  
A: Creating a new TCP connection for every query is extremely expensive (TCP handshake, TLS negotiation, Bolt protocol negotiation, authentication). Connection pooling amortizes this cost across hundreds of queries.
