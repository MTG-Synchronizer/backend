import asyncio
import argparse
import json
from utils.ingest import chunk_iterable, get_settings
from neo4j import AsyncGraphDatabase, AsyncManagedTransaction, AsyncSession
from codetiming import Timer

from utils.card import get_formatted_card


def load_data(file_name: str) -> list:
    base_url = "data/mtg_goldfish/"
    with open(base_url + file_name, "r") as f:
        data = json.load(f)

    decks = []
    for category in data:
        for deck in data[category]:
            cards = data[category][deck]
            cards = [get_formatted_card(card[1])[0] for card in cards]
            decks.append(cards)
    
    return decks


# Modified to take multiple relationships in a single transaction
async def create_or_update_relationships(tx: AsyncManagedTransaction, pairs: list):
    query = """
    UNWIND $pairs AS pair
    MATCH (a:Card), (b:Card)
    WHERE (a.name_front = pair[0] OR a.full_name = pair[0])
        AND (b.name_front = pair[1] OR b.full_name = pair[1])
    MERGE (a)-[r:CONNECTED]-(b)
    ON CREATE SET r.sync = 1
    ON MATCH SET r.sync = r.sync + 1
    """
    await tx.run(query, pairs=pairs)


async def get_unique_pairs_in_deck(deck):
    pairs = []
    # Iterate through each unique pair in the list
    for i in range(len(deck)):
        for j in range(i + 1, len(deck)):
            pairs.append([deck[i], deck[j]])
    return pairs



async def ingest_data(session: AsyncSession, data: dict):
    chunked_data = chunk_iterable(data, CHUNKSIZE)
    print("Ingesting data...")
    with Timer(name="ingest"):
        for idx, chunk in enumerate(chunked_data):
            # Awaiting each chunk in a loop isn't ideal, but it's easiest this way when working with graphs!
            # Merging edges on top of nodes concurrently can lead to race conditions. Neo4j doesn't allow this,
            # and prevents the user from merging relationships on nodes that might not exist yet, for good reason.
            try:
                unique_pairs = []
                for deck in chunk:
                    unique_pairs.extend(await get_unique_pairs_in_deck(deck))

                await session.execute_write(create_or_update_relationships, unique_pairs)
                print(f"Processed chunk {idx + 1}")

            except Exception as e:
                print(f"{e}: Failed to ingest chunk #{idx + 1}")


async def main(metagame_data: dict, custom_data: dict):
    async with AsyncGraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        async with driver.session(database="neo4j") as session:
            print("Ingesting metagame data")
            await ingest_data(session, metagame_data)
            print("Ingesting custom data")
            await ingest_data(session, custom_data)


if __name__ == "__main__":
    # fmt: off
    parser = argparse.ArgumentParser("Load MTG Goldfish decklists into Neo4j")
    parser.add_argument("--chunksize", type=int, default=100, help="Size of each chunk to break the dataset into before processing")
    args = vars(parser.parse_args())
    # fmt: on

    # Neo4j setup
    settings = get_settings()
    URI = f"bolt://{settings.SERVER_HOST}:7687"
    NEO4J_USER = settings.NEO4J_USER
    NEO4J_PASSWORD = settings.NEO4J_PASSWORD
    CHUNKSIZE = args["chunksize"]

    metagame_data = load_data("metagame.json")
    custom_data = load_data("custom.json")

    if metagame_data and custom_data:
        # Use uvloop for potential performance gains
        import uvloop
        uvloop.install()
        asyncio.run(main(metagame_data, custom_data))