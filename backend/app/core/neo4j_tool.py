"""This file's job is only to define the tool and execute the query."""

"""
Neo4j tool for Gemini function calling.
"""

from app.core.neo4j_connector import neo4j_connector


def execute_neo4j_query(cypher_query: str):
    """
    Executes a Cypher query against the Neo4j database.
    """
    return neo4j_connector.run_query(cypher_query)