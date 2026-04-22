from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7688")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "cortex_secure_graph_99!")

driver = GraphDatabase.driver(uri, auth=(username, password))

def test_create_index():
    with driver.session() as session:
        session.run("DROP INDEX test_vector_index IF EXISTS")
        query = """
        CREATE VECTOR INDEX test_vector_index FOR (e:Entity) ON (e.embedding)
        WITH [e.session_id, e.is_active]
        OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}
        """
        session.run(query)
        print("Success!")

if __name__ == "__main__":
    try:
        test_create_index()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()
