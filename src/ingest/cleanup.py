
from utils.ingest import get_settings
from neo4j import GraphDatabase, ManagedTransaction

def cleanup(tx: ManagedTransaction):
    # Delete all relationships that target themselves
    query = """
    MATCH (n)-[r]-(n)
    DELETE r
    """
    tx.run(query)

    # Set total_recurrences property on Card nodes
    query = """
    MATCH (c:Card)-[r:CONNECTED]-(:Card)
    WITH c, SUM(r.sync) AS totalSync
    SET c.total_recurrences = totalSync
    """
    tx.run(query)


if __name__ == "__main__":
    # # Neo4j
    settings = get_settings()
    URI = f"bolt://{settings.NEO4J_URL}:7687"
    NEO4J_USER = settings.NEO4J_USER
    NEO4J_PASSWORD = settings.NEO4J_PASSWORD

    
    with GraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session(database="neo4j") as session:
            session.execute_write(cleanup)