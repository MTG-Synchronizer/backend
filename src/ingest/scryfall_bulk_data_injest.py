import argparse
import asyncio
import requests
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

from pydantic import ValidationError
from codetiming import Timer
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase, AsyncManagedTransaction, AsyncSession

sys.path.insert(1, os.path.realpath(Path(__file__).resolve().parents[1]))
from config.settings import Settings
from schemas.mtg_card import MtgCard

# Custom types
JsonBlob = dict[str, Any]


class FileNotFoundError(Exception):
    pass


# --- Blocking functions ---

@lru_cache()
def get_settings():
    load_dotenv()
    # Use lru_cache to avoid loading .env file for every request
    return Settings()


def chunk_iterable(item_list: list[JsonBlob], chunksize: int) -> Iterator[list[JsonBlob]]:
    """
    Break a large iterable into an iterable of smaller iterables of size `chunksize`
    """
    for i in range(0, len(item_list), chunksize):
        yield item_list[i : i + chunksize]

@Timer(name="pydantic validator")
def validate(
    data: list[JsonBlob],
    exclude_none: bool = False,
) -> list[JsonBlob]:
    validated_data = [MtgCard(**item).model_dump(exclude_none=exclude_none) for item in data]
    return validated_data


def fetch_url(url: str) -> dict:
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
    # Parse the HTML content
        return response.json()
    else:
        raise Exception(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    

def get_scryfall_bulk_data(url):
    response = fetch_url(url)

    for obj in response['data']:
        if obj['type'] == 'oracle_cards':
            return fetch_url(obj['download_uri'])


# --- Async functions ---


async def create_indexes_and_constraints(session: AsyncSession) -> None:
    queries = [
        # constraints
        "CREATE CONSTRAINT name IF NOT EXISTS FOR (c:Card) REQUIRE c.name IS UNIQUE ",
        # indexes
        "CREATE INDEX oracle_id IF NOT EXISTS FOR (c:Card) ON (c.oracle_id) ",
        ]
    for query in queries:
         await session.run(query)


async def build_query(tx: AsyncManagedTransaction, data: list[JsonBlob]) -> None:
    query = """
        UNWIND $data AS record
        MERGE (c:Card {name: record.name})
        SET
            c.name = record.name,
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
    URI = f"bolt://{settings.neo4j_url}:7687"
    NEO4J_USER = settings.neo4j_user
    NEO4J_PASSWORD = settings.neo4j_password
    

    data = list(get_scryfall_bulk_data(SCRYFALL_BULK_DATA_URL))
    if LIMIT > 0:
        data = data[:LIMIT]

    if data:
        # Neo4j async uses uvloop under the hood, so we can gain marginal performance improvement by using it too
        import uvloop

        uvloop.install()
        asyncio.run(main(data))