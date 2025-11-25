from neo4j import GraphDatabase

URI = "bolt://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "mastermaster"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

with driver.session(database="neo4j") as session:
    result = session.run("MATCH (n) RETURN count(n) AS c").single()
    print("Liczba węzłów przed:", result["c"])

    session.run("MATCH (n) DETACH DELETE n")
    result2 = session.run("MATCH (n) RETURN count(n) AS c").single()
    print("Liczba węzłów po:", result2["c"])

driver.close()
