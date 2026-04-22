from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7688")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "cortex_secure_graph_99!")

driver = GraphDatabase.driver(uri, auth=(username, password))

def check_indices():
    with driver.session() as session:
        result = session.run("SHOW VECTOR INDEXES")
        for record in result:
            print(record)

if __name__ == "__main__":
    try:
        check_indices()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()
