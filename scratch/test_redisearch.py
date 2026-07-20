from graph_cortex.infrastructure.db.falkordb_connection import get_graph
from graph_cortex.infrastructure.db.queries.retrieval_queries import get_anchors_by_fulltext

graph = get_graph()
# test OR query
res2 = get_anchors_by_fulltext(graph, "where | did | jason | store | his | keys", session_id="e2e_memory_bench")
print("OR Query:", res2)
