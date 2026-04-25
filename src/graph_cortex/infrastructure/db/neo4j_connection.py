import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            uri = os.getenv("NEO4J_URI")
            username = os.getenv("NEO4J_USERNAME")
            password = os.getenv("NEO4J_PASSWORD")

            if not all([uri, username, password]):
                print("[ERROR] Neo4j config missing — set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env")
                cls._instance.driver = None
                return cls._instance

            try:
                cls._instance.driver = GraphDatabase.driver(uri, auth=(username, password))
            except Exception as e:
                print(f"[ERROR] Neo4j connection failed: {e}")
                cls._instance.driver = None
        return cls._instance

    def close(self):
        if self.driver:
            self.driver.close()

    def get_driver(self):
        return self.driver


db_connection = Neo4jConnection()


def get_session():
    driver = db_connection.get_driver()
    if driver:
        return driver.session()
    raise ConnectionError("Neo4j driver not initialized")


def execute_read_query(query: str, **kwargs):
    with get_session() as session:
        result = session.run(query, **kwargs)
        return [record.data() for record in result]
