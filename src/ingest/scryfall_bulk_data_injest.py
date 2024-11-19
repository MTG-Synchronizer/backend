import argparse
import asyncio
import os
import sys

from pathlib import Path
from typing import Any

from codetiming import Timer
from neo4j import AsyncGraphDatabase, AsyncManagedTransaction, AsyncSession

sys.path.insert(1, os.path.realpath(Path(__file__).resolve().parents[1]))
from schemas.db.mtg_card import MtgCard
from utils.request import fetch_url
from utils.ingest import chunk_iterable, get_settings


# Custom types
JsonBlob = dict[str, Any]

@Timer(name="pydantic validator")
def validate(
    data: list[JsonBlob],
    exclude_none: bool = False,
) -> list[JsonBlob]:
    validated_data = [MtgCard(**item).model_dump(exclude_none=exclude_none) for item in data]
    return validated_data
    

def get_scryfall_bulk_data(url):
    response = fetch_url(url)

    for obj in response['data']:
        if obj['type'] == 'oracle_cards':
            return fetch_url(obj['download_uri'])


# --- Async functions ---


async def create_indexes_and_constraints(session: AsyncSession) -> None:
    queries = [
        # constraints
        "CREATE CONSTRAINT full_name IF NOT EXISTS FOR (c:Card) REQUIRE c.full_name IS UNIQUE",
        "CREATE CONSTRAINT name_front IF NOT EXISTS FOR (c:Card) REQUIRE c.name_front IS UNIQUE",

        # indexes
        "CREATE INDEX oracle_id IF NOT EXISTS FOR (c:Card) ON (c.oracle_id) ",
        "CREATE INDEX price_usd IF NOT EXISTS FOR (c:Card) ON (c.price_usd) ",
        ]
    for query in queries:
         await session.run(query)


async def build_query(tx: AsyncManagedTransaction, data: list[JsonBlob]) -> None:
    query = """
        UNWIND $data AS record
        WITH record,
            split(toUpper(record.name), " // ") AS names,
            apoc.text.split(record.type_line, " // | — ") AS types
        MERGE (c:Card {name_front: names[0]})
        SET
            c.full_name = toUpper(record.name),
            c.name_front = names[0],
            c.name_back = names[1],

            c.types = types,

            c.oracle_id = record.oracle_id,
            c.colors = record.colors,
            c.cmc = record.cmc,
            c.keywords = record.keywords,
            c.rarity = record.rarity,

            c.price_usd = record.prices.usd,
            c.price_usd_foil = record.prices.usd_foil,
            c.price_eur = record.prices.eur,
            c.price_tix = record.prices.tix,

            c.legality_standard = record.legalities.standard,
            c.legality_future = record.legalities.future,
            c.legality_historic = record.legalities.historic,
            c.legality_timeless = record.legalities.timeless,
            c.legality_gladiator = record.legalities.gladiator,
            c.legality_pioneer = record.legalities.pioneer,
            c.legality_explorer = record.legalities.explorer,
            c.legality_modern = record.legalities.modern,
            c.legality_legacy = record.legalities.legacy,
            c.legality_pauper = record.legalities.pauper,
            c.legality_vintage = record.legalities.vintage,
            c.legality_penny = record.legalities.penny,
            c.legality_commander = record.legalities.commander,
            c.legality_oathbreaker = record.legalities.oathbreaker,
            c.legality_standardbrawl = record.legalities.standardbrawl,
            c.legality_brawl = record.legalities.brawl,
            c.legality_alchemy = record.legalities.alchemy,
            c.legality_paupercommander = record.legalities.paupercommander,
            c.legality_duel = record.legalities.duel,
            c.legality_oldschool = record.legalities.oldschool,
            c.legality_premodern = record.legalities.premodern
        RETURN c
        """
    await tx.run(query, data=data)


def convert_oracle_id_to_string(data: list[dict]) -> list[dict]:
    for record in data:
        record["oracle_id"] = str(record["oracle_id"])
    return data

async def main(data: list[JsonBlob]) -> None:
    async with AsyncGraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        async with driver.session(database="neo4j") as session:
            # Create indexes and constraints
            await create_indexes_and_constraints(session)
            # Ingest the data into Neo4j
            print("Validating data...")
            validated_data = validate(data, exclude_none=True)
            validated_data = convert_oracle_id_to_string(validated_data)
            
            # Break the data into chunks
            chunked_data = chunk_iterable(validated_data, CHUNKSIZE)
            print("Ingesting data...")
            with Timer(name="ingest"):
                for idx, chunk in enumerate(chunked_data):
                    # Awaiting each chunk in a loop isn't ideal, but it's easiest this way when working with graphs!
                    # Merging edges on top of nodes concurrently can lead to race conditions. Neo4j doesn't allow this,
                    # and prevents the user from merging relationships on nodes that might not exist yet, for good reason.
                    try:
                        await session.execute_write(build_query, chunk)
                        print(f"Processed chunk #{idx + 1}")
                    except Exception as e:
                        print(f"{e}: Failed to ingest chunk #{idx + 1}")


if __name__ == "__main__":
    # fmt: off
    parser = argparse.ArgumentParser("Build a graph of MTG cards from Scryfall Bulk Data")
    parser.add_argument("--limit", type=int, default=0, help="Limit the size of the dataset to load for testing purposes")
    parser.add_argument("--chunksize", type=int, default=10_000, help="Size of each chunk to break the dataset into before processing")
    args = vars(parser.parse_args())
    # fmt: on

    LIMIT = args["limit"]
    CHUNKSIZE = args["chunksize"]
    SCRYFALL_BULK_DATA_URL = "https://api.scryfall.com/bulk-data"

    # # Neo4j
    settings = get_settings()
    URI = f"bolt://{settings.NEO4J_URL}:7687"
    NEO4J_USER = settings.NEO4J_USER
    NEO4J_PASSWORD = settings.NEO4J_PASSWORD
    

    data = list(get_scryfall_bulk_data(SCRYFALL_BULK_DATA_URL))
    if LIMIT > 0:
        data = data[:LIMIT]

    if data:
        # Neo4j async uses uvloop under the hood, so we can gain marginal performance improvement by using it too
        import uvloop

        uvloop.install()
        asyncio.run(main(data))