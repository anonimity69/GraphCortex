from graph_cortex.infrastructure.db.neo4j_connection import get_session

def check_graph():
    with get_session() as session:
        print("--- Node List ---")
        result = session.run("MATCH (n) RETURN labels(n)[0] as label, n.name as name, n.session_id as sid")
        for r in result:
            print(f"[{r['label']}] {r['name']} (sid: {r['sid']})")
            
        print("\n--- Relationship List ---")
        result = session.run("MATCH (n)-[r]->(m) RETURN n.name as start, type(r) as rel, m.name as end")
        for r in result:
            print(f"{r['start']} -[:{r['rel']}]-> {r['end']}")

if __name__ == "__main__":
    check_graph()
