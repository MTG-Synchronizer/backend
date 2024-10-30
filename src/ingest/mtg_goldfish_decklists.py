import asyncio
import json
from ingest.utils import chunk_iterable, get_settings
from neo4j import AsyncGraphDatabase, AsyncManagedTransaction, AsyncSession
from codetiming import Timer


async def create_or_update_relationship(tx: AsyncManagedTransaction, node1: str, node2: str):
    query = """
    MERGE (a:Card {name: $node1})
    MERGE (b:Card {name: $node2})
    MERGE (a)-[r:CONNECTED]-(b)
    ON CREATE SET r.sync = 1
    ON MATCH SET r.sync = r.sync + 1
    """
    await tx.run(query, node1=node1, node2=node2)

async def bidirectional_connect(session: AsyncSession, node_names: list):
    for i in range(len(node_names)):
        for j in range(i + 1, len(node_names)):
            node1 = node_names[i][1]
            node2 = node_names[j][1]
            # Debug statement to check node names
            await session.execute_write(create_or_update_relationship, node1, node2)

async def ingest_data(session: AsyncSession, data: dict):
    for category in data:
        for deck in data[category]:
            cards = data[category][deck]
            print(f"Ingesting deck {deck}")
            await bidirectional_connect(session, cards)


async def main(metagame_data: dict, custom_data: dict):
    async with AsyncGraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        async with driver.session(database="neo4j") as session:
            print("Ingesting metagame data")
            await ingest_data(session, metagame_data)
            print("Ingesting custom data")
            await ingest_data(session, custom_data)

if __name__ == "__main__":

    # # Neo4j
    settings = get_settings()
    URI = f"bolt://{settings.neo4j_url}:7687"
    NEO4J_USER = settings.neo4j_user
    NEO4J_PASSWORD = settings.neo4j_password

    with open("data/mtg_goldfish/metagame.json", "r") as f:
        metagame_data = json.load(f)
    
    with open("data/mtg_goldfish/custom.json", "r") as f:
        custom_data = json.load(f)

    
    if metagame_data and custom_data:
        # Neo4j async uses uvloop under the hood, so we can gain marginal performance improvement by using it too
        import uvloop
        uvloop.install()
        asyncio.run(main(metagame_data, custom_data))