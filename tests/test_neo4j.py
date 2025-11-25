import os

from neo4j import GraphDatabase
from dotenv import load_dotenv


load_dotenv()
URI = os.environ.get("NEO4J_URI")
USER = os.environ.get("NEO4J_USER")
PASSWORD = os.environ.get("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

with driver.session(database="neo4j") as session:
    result = session.run("MATCH (n) RETURN count(n) AS c").single()
    print("Liczba węzłów przed:", result["c"])

    session.run("MATCH (n) DETACH DELETE n")
    result2 = session.run("MATCH (n) RETURN count(n) AS c").single()
    print("Liczba węzłów po:", result2["c"])

driver.close()
