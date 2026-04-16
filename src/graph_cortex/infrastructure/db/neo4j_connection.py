import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jConnection:
    _instance = None # Singleton pattern to ensure only one connection is created
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
            uri = os.getenv("NEO4J_URI")
            username = os.getenv("NEO4J_USERNAME")
            password = os.getenv("NEO4J_PASSWORD")
            
            # Enforce configuration — no hardcoded fallbacks for security
            if not all([uri, username, password]):
                error_msg = "[ERROR] Missing Neo4j Configuration. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file."
                print(error_msg)
                cls._instance.driver = None
                return cls._instance

            try:
                cls._instance.driver = GraphDatabase.driver(uri, auth=(username, password))
            except Exception as e:
                print(f"[ERROR] Failed to connect to Neo4j: {e}")
                cls._instance.driver = None
        return cls._instance

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def get_driver(self):
        return self.driver

# Global connection instance
db_connection = Neo4jConnection()

def get_session():
    """Returns a Neo4j session"""
    driver = db_connection.get_driver()
    if driver:
        return driver.session()
    raise ConnectionError("Neo4j driver is not initialized.")

def execute_read_query(query: str, **kwargs):
    """Executes a generic read transaction and returns a list of dictionaries."""
    with get_session() as session:
        result = session.run(query, **kwargs)
        return [record.data() for record in result]
