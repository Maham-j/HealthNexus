"""
Thin wrapper around the official neo4j Python driver.
Everything else in the app should go through this, not import neo4j directly,
so we only have one place that knows about connection details.
"""
from neo4j import GraphDatabase
from app.config import settings


class Neo4jConnector:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self):
        self._driver.close()

    def run_query(self, cypher: str, params: dict | None = None) -> list[dict]:
        """
        Run a Cypher query and return results as a list of plain dicts.
        This is what the LLM's generated Cypher will ultimately call.
        """
        params = params or {}
        with self._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]

    def verify_connection(self) -> bool:
        try:
            with self._driver.session(database=settings.neo4j_database) as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            return False


# Single shared instance used across the app
neo4j_connector = Neo4jConnector()
