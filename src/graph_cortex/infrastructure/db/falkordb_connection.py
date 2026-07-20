import os
from falkordb import FalkorDB
from dotenv import load_dotenv

load_dotenv()


class FalkorDBConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            host = os.getenv("FALKORDB_HOST", "127.0.0.1")
            port = int(os.getenv("FALKORDB_PORT", 6379))
            graph_name = os.getenv("FALKORDB_GRAPH", "graphcortex")

            try:
                cls._instance.db = FalkorDB(host=host, port=port)
                cls._instance.graph_name = graph_name
                cls._instance._graph = cls._instance.db.select_graph(graph_name)
            except Exception as e:
                print(f"[ERROR] FalkorDB connection failed: {e}")
                cls._instance.db = None
                cls._instance._graph = None
        return cls._instance

    def close(self):
        if self.db:
            self.db.close()

    def get_graph(self):
        return self._graph


db_connection = FalkorDBConnection()


class DictResult:
    """Adapter that wraps FalkorDB query results to provide dict-style access.

    FalkorDB returns results as (header, result_set) where result_set is a list
    of tuples. This adapter converts them to a list of dicts keyed by column name,
    matching the Neo4j driver's record.data() interface.
    """

    def __init__(self, result):
        self._result = result
        self._header = [h[1] if isinstance(h, list) and len(h) > 1 else h for h in result.header] if result and result.header else []
        self._rows = result.result_set if result and result.result_set else []

    def data(self):
        """Return all rows as a list of dicts."""
        return [
            {self._header[i]: row[i] for i in range(len(self._header))}
            for row in self._rows
        ]

    def single(self):
        """Return the first row as a dict, or None if empty."""
        if self._rows:
            return {self._header[i]: self._rows[0][i] for i in range(len(self._header))}
        return None

    def __iter__(self):
        for row in self._rows:
            yield {self._header[i]: row[i] for i in range(len(self._header))}

    def __len__(self):
        return len(self._rows)


def get_graph():
    """Get the FalkorDB graph handle. Raises if not connected."""
    graph = db_connection.get_graph()
    if graph is None:
        raise ConnectionError("FalkorDB graph not initialized")
    return graph


def execute_query(query: str, params: dict = None):
    """Execute a Cypher query and return a DictResult adapter."""
    graph = get_graph()
    result = graph.query(query, params=params)
    return DictResult(result)


def execute_read_query(query: str, **kwargs):
    """Execute a read query and return results as a list of dicts."""
    return execute_query(query, params=kwargs).data()
