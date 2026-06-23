import os
from neo4j import GraphDatabase as Neo4jDriver

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

def ensure_indexes():
    """Create indexes on Neo4j for node_id and name properties to optimize search/merge lookups."""
    driver = Neo4jDriver.driver(NEO4J_URI, auth=NEO4J_AUTH)
    queries = [
        "CREATE CONSTRAINT UNIQUE_individual_node_id IF NOT EXISTS FOR (n:Individual) REQUIRE n.node_id IS UNIQUE",
        "CREATE CONSTRAINT UNIQUE_organization_node_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.node_id IS UNIQUE",
        "CREATE CONSTRAINT UNIQUE_crime_node_id IF NOT EXISTS FOR (n:Crime) REQUIRE n.node_id IS UNIQUE",
        "CREATE CONSTRAINT UNIQUE_protest_node_id IF NOT EXISTS FOR (n:Protest) REQUIRE n.node_id IS UNIQUE",
        "CREATE CONSTRAINT UNIQUE_record_node_id IF NOT EXISTS FOR (n:Record) REQUIRE n.node_id IS UNIQUE",
        "CREATE CONSTRAINT UNIQUE_case_node_id IF NOT EXISTS FOR (n:Case) REQUIRE n.node_id IS UNIQUE",
        "CREATE INDEX individual_name_idx IF NOT EXISTS FOR (n:Individual) ON (n.name)"
    ]
    with driver.session(database=NEO4J_DATABASE) as session:
        for q in queries:
            try:
                session.run(q)
            except Exception as e:
                # Neo4j < 4.4 uses different constraint syntax, fallback to index if constraint fails
                # or just print a warning. In Neo4j 5, the syntax is REQUIRE ... IS UNIQUE.
                print(f"[Warning] Index/Constraint creation failed: {e}")
    driver.close()
