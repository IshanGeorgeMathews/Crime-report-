import os
import sys
# Ensure core directory is on path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_dir, "core"))

from neo4j import GraphDatabase
from graph_db import load_env

# Load local environment configuration
load_env()

uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "DigitalUniversity")

driver = GraphDatabase.driver(uri, auth=(user, password))
driver.verify_connectivity()
print("Connected")