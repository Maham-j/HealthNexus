"""
Neo4j connector — TODO: implement connection logic.
"""


class Neo4jConnector:
    def __init__(self):
        pass

    def run_query(self, cypher: str, params: dict = None):
        raise NotImplementedError

    def verify_connection(self) -> bool:
        raise NotImplementedError
