
from utils.db_processing import get_settings
from neo4j import GraphDatabase, ManagedTransaction


def clear_clusters(tx: ManagedTransaction):
    # Remove old projections if they exist
    query = """
    CALL gds.graph.drop('card-similarities', false)
    """
    tx.run(query)

    query="""
    MATCH (c:CardCommunity)
    DETACH DELETE c
    """
    tx.run(query)

    query="""
    MATCH (c:Card)
    REMOVE c.communityId;
    """

def create_clusters(tx: ManagedTransaction):
    

    # set up a graph projection for analysis
    query ="""
    CALL gds.graph.project(
        'card-similarities',
        'Card',
        {
            CONNECTED: {
                orientation: 'UNDIRECTED',
                properties: ['dynamicWeight']
            }
        }
    );
    """
    tx.run(query)

    # Run Louvain algorithm for community detection
    query = """
    CALL gds.louvain.write(
        'card-similarities',
        {
            writeProperty: 'communityId',
            relationshipWeightProperty: 'dynamicWeight',
            includeIntermediateCommunities: true
        }
    )
    YIELD communityCount, modularity;
    """
    tx.run(query)

    # Update community relationships
    query = """
    MATCH (c:Card)
    WHERE c.communityId IS NOT NULL
    WITH c, c.communityId AS communityId
    MERGE (community:CardCommunity {id: communityId})
    CREATE (c)-[:BELONGS_TO]->(community);
    """
    tx.run(query)

def handle_clusters(tx: ManagedTransaction):
    clear_clusters(tx)
    create_clusters(tx)
    



if __name__ == "__main__":
    # # Neo4j
    settings = get_settings()
    URI = f"bolt://{settings.SERVER_HOST}:7687"
    NEO4J_USER = settings.NEO4J_USER
    NEO4J_PASSWORD = settings.NEO4J_PASSWORD

    
    with GraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session(database="neo4j") as session:
            session.execute_write(handle_clusters)