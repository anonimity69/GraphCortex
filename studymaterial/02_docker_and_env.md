# Module 02: Docker & Environment Configuration

## Files Covered
- `docker-compose.yml`
- `.env`
- `.env.example`

---

---
**What it does:** Declares the Docker Compose file format version. Version 3.8 is the most widely supported modern format.

```yaml
services:
  neo4j:
    image: neo4j:5.18.1
```
**What it does:** Defines a service named `neo4j` that runs the official Neo4j Docker image, pinned to version `5.18.1`. Pinning the version (not using `latest`) prevents unexpected breaking changes when rebuilding containers.

**Client question:** *"Why 5.18.1 specifically?"*  
**Answer:** *"Neo4j 5.x introduced native Vector Index support, which we need for Phase 3 semantic search. We pin the version for reproducibility."*

```yaml
    container_name: neo4j_nsdmg
```
**What it does:** Gives the container a human-readable name instead of a random hash. Makes `docker logs neo4j_nsdmg` and `docker exec neo4j_nsdmg` much easier.

```yaml
```yaml
    ports:
      - "7475:7474" # HTTP port for Neo4j Browser
      - "7688:7687" # Bolt port
```
**What it does:** Maps container ports to your local machine.
- **7475** → Neo4j Browser (the web UI at `http://localhost:7475`)
- **7688** → Bolt protocol (used by the Python driver)

```yaml
    environment:
      - NEO4J_AUTH=${NEO4J_USERNAME}/${NEO4J_PASSWORD}
```
**What it does:** Sets the Neo4j authentication credentials using variables from your `.env` file. The format is `username/password`. When the container starts for the **first time**, it permanently saves this password into the data volume. This is why changing `.env` alone won't work after the first boot — you need to wipe the data volume.

```yaml
      - NEO4J_apoc_export_file_enabled=true
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_apoc_import_file_use__neo4j__config=true
```
**What it does:** Enables APOC (Awesome Procedures On Cypher) file import/export capabilities. APOC is a plugin library that extends Cypher with utility procedures. The double underscores `__` map to dots in Neo4j config (`apoc.import.file.use_neo4j_config`).

```yaml
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
```
**What it does:** Automatically installs two critical plugins:
- **APOC** — Provides conditional procedures like `apoc.do.when` (now deprecated, we migrated to native Cypher)
- **Graph Data Science (GDS)** — Provides graph algorithms (PageRank, community detection, etc.) for future phases

```yaml
    volumes:
      - ./data/neo4j/data:/data
      - ./data/neo4j/logs:/logs
      - ./data/neo4j/import:/var/lib/neo4j/import
      - ./data/neo4j/plugins:/plugins
```
**What it does:** Persists Neo4j data to your local filesystem. Without volumes, all data would be lost when the container restarts. The `./data/neo4j/data` directory contains the actual database files — **this is why wiping this directory resets the password**.

```yaml
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:7474 || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 10
```
**What it does:** Docker periodically checks if Neo4j is healthy by hitting the HTTP endpoint. If it fails 5 times in a row, Docker marks the container as unhealthy. This is useful for orchestration tools (Kubernetes, etc.) that need to know if the service is genuinely ready.

---

## .env — The Connection Credentials

```env
NEO4J_URI=bolt://127.0.0.1:7688
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=cortex_secure_graph_99!
```

### Key Details

| Variable | Value | Explanation |
|---|---|---|
| `NEO4J_URI` | `bolt://127.0.0.1:7688` | The connection URI. We use `7688` on the host to avoid conflict with local Neo4j Desktop (7687). |
| `NEO4J_USERNAME` | `neo4j` | The default admin username. Neo4j always creates this user on first boot. |
| `NEO4J_PASSWORD` | `cortex_secure_graph_99!` | The password you set when creating the database. |

### Why `.env` exists separately from `docker-compose.yml`
The `.env` file is loaded by **both** Docker Compose (for the container) and the Python application (via `python-dotenv`). This "single source of truth" pattern prevents credential drift — you never have one password in Docker and a different one in Python.

### Security Note
The `.env` file is listed in `.gitignore` so credentials are never committed to version control. The `.env.example` file provides a safe template for new developers.
