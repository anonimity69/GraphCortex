from graph_cortex.infrastructure.db.falkordb_connection import get_graph
graph = get_graph()
q = """
MATCH (n)-[r]->(m) 
WHERE n.session_id = 'e2e_memory_bench' 
RETURN n.name, type(r), m.name
"""
res = graph.query(q)
for r in res.result_set:
    print(r)
