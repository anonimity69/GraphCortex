from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Test both bolt and neo4j schemes
schemes = ["bolt", "neo4j"]
port = 7688
username = "neo4j"
password = "cortex_secure_graph_99!"

for scheme in schemes:
    uri = f"{scheme}://127.0.0.1:{port}"
    print(f"Testing {uri}...")
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 1")
            print(f"  Success with {scheme}!")
        driver.close()
    except Exception as e:
        print(f"  Failed with {scheme}: {e}")
