# Changelog

## 0.2.2 — 2026-07-21

Documentation only. Absolute asset URLs so the README renders on PyPI, `pip install`
instructions in the quickstart, and removal of the demo video. No code changes.

## 0.2.1 — 2026-07-21

Packaging metadata for PyPI distribution. No code changes.

## 0.2.0 — 2026-07-21

Migrates the graph backend from Neo4j to FalkorDB, fixes literal-value recall in the
retrieval path, and hardens the LLM client against rate limits.

### Database

- **Replaces Neo4j with FalkorDB.** The Redis-backed GraphBLAS engine starts in under a
  second where the Neo4j JVM took 30–45s, deploys as a single container with a built-in
  graph browser, and its sparse-matrix representation maps naturally onto the traversal
  patterns the retrieval engine already used.
- Cypher compatibility was close enough (~95%) that the migration required no changes to
  query structure beyond FalkorDB-specific index syntax and the `:Searchable` super-label
  workaround for multi-label fulltext indexes.
- No head-to-head benchmark against the Neo4j backend was recorded before it was removed,
  so this release makes no quantified throughput or latency claim.

### Agent memory & recall

- **Fixes a failure mode where the Researcher could locate the correct memory node but not
  recall its literal contents** — API keys, codenames, exact timestamps. Anchor and
  traversal queries now return `properties(node)`, and the Researcher injects those scalar
  values verbatim into the LLM context rather than only the node's name and type.
- Node properties are now carried through the entire retrieval path: anchor lookup, A*
  expansion, lateral inhibition, and edge reconstruction.

### Reliability

- **The LLM client now retries on 429 / `RESOURCE_EXHAUSTED`.** It parses the server's
  suggested retry delay out of the error message and waits that long, capped at 60s,
  falling back to 25s when no hint is present. Up to 3 retries.
- The CLI no longer crashes when the model returns an empty response after a safety block.
  The Researcher substitutes an explicit error string instead.
- Fixes a missing logger reference that suppressed debug output during retrieval.

### Repository

- Removes roughly 20 legacy debug scripts, the RL training dataset, and model weights from
  the working tree, cutting checkout size. These blobs remain in git history, so clone
  size is unchanged.
- Rewrites the README as a product landing page and adds `DECISIONS.md` documenting the
  architectural rationale behind each major choice.

### Known gaps

- **Lateral inhibition does not suppress hub nodes on the A* retrieval path.** Node degree
  is hardcoded rather than computed, so the degree term of the activation-decay function
  is constant across nodes. It works as intended only on the fallback spreading-activation
  path. Tracked for 0.3.0.
- **The RL training loop is a bootstrap, not a closed-loop eval.** The reward judge is fed
  ground truth in place of a real agent answer, so the learned signal is weak. The
  Librarian's action selection runs as designed; the policy behind it is undertrained.
- **No policy weights ship with the repository.** A fresh clone runs the Librarian with a
  randomly initialized policy until you run `/train`.
- The CLI opens every session with a fixed session ID, so separate installations pointed at
  a shared FalkorDB instance will share memory.
