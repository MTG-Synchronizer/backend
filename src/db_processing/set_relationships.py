
from utils.db_processing import get_settings
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

    # Set dynamicWeight based on square root scaling
    # Perform query by periodic iteration
    query = """
    CALL apoc.periodic.iterate(
        "MATCH (c:Card)-[r:CONNECTED]-(other:Card) RETURN c, r, other",
        "SET r.dynamicWeight = r.sync * 1.0 / sqrt(c.total_recurrences + other.total_recurrences)",
    {batchSize: 1000, parallel: true}
    )
    """
    tx.run(query)


if __name__ == "__main__":
    # # Neo4j
    settings = get_settings()
    URI = f"bolt://{settings.SERVER_HOST}:7687"
    NEO4J_USER = settings.NEO4J_USER
    NEO4J_PASSWORD = settings.NEO4J_PASSWORD

    
    with GraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session(database="neo4j") as session:
            session.execute_write(cleanup)