"""
Quick standalone check: run this after setting up .env to confirm
the app can actually reach your Neo4j instance before building anything
on top of it.

Usage: make check-neo4j
"""
import sys
from app.core.neo4j_connector import neo4j_connector


def main():
    print("Checking Neo4j connection...")
    ok = neo4j_connector.verify_connection()
    if ok:
        print("✅ Connected successfully.")
        rows = neo4j_connector.run_query("MATCH (n) RETURN count(n) AS total_nodes")
        print(f"Total nodes in database: {rows[0]['total_nodes']}")
        sys.exit(0)
    else:
        print("❌ Could not connect. Check your .env NEO4J_* values.")
        sys.exit(1)


if __name__ == "__main__":
    main()
