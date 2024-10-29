import argparse
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import srsly
from codetiming import Timer
from dotenv import load_dotenv
from neo4j import GraphDatabase, ManagedTransaction, Session

sys.path.insert(1, os.path.realpath(Path(__file__).resolve().parents[1]))
from config.settings import Settings
from schemas.wine import Wine


# Custom types
JsonBlob = dict[str, Any]


class FileNotFoundError(Exception):
    pass


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


def get_json_data(data_dir: Path, filename: str) -> list[JsonBlob]:
    """Get all line-delimited json files (.jsonl) from a directory with a given prefix"""
    file_path = data_dir / filename
    if not file_path.is_file():
        # File may not have been uncompressed yet so try to do that first
        data = srsly.read_gzip_jsonl(file_path)
        # This time if it isn't there it really doesn't exist
        if not file_path.is_file():
            raise FileNotFoundError(f"No valid .jsonl file found in `{data_dir}`")
    else:
        data = srsly.read_gzip_jsonl(file_path)
    return data


@Timer(name="pydantic validator")
def validate(
    data: list[JsonBlob],
    exclude_none: bool = False,
) -> list[JsonBlob]:
    validated_data = [Wine(**item).model_dump(exclude_none=exclude_none) for item in data]
    return validated_data


def create_indexes_and_constraints(session: Session) -> None:
    queries = [
        # constraints
        "CREATE CONSTRAINT countryName IF NOT EXISTS FOR (c:Country) REQUIRE c.countryName IS UNIQUE ",
        "CREATE CONSTRAINT wineID IF NOT EXISTS FOR (w:Wine) REQUIRE w.wineID IS UNIQUE ",
        # indexes
        "CREATE INDEX provinceName IF NOT EXISTS FOR (p:Province) ON (p.provinceName) ",
        "CREATE INDEX tasterName IF NOT EXISTS FOR (p:Person) ON (p.tasterName) ",
        "CREATE FULLTEXT INDEX searchText IF NOT EXISTS FOR (w:Wine) ON EACH [w.title, w.description, w.variety] ",
    ]
    for query in queries:
         session.run(query)


def build_query(tx: ManagedTransaction, data: list[JsonBlob]) -> None:
    query = """
        UNWIND $data AS record
        MERGE (wine:Wine {wineID: record.id})
            SET wine += {
                points: record.points,
                title: record.title,
                description: record.description,
                price: record.price,
                variety: record.variety,
                winery: record.winery,
                vineyard: record.vineyard,
                region_1: record.region_1,
                region_2: record.region_2
            }
        WITH record, wine
            WHERE record.taster_name IS NOT NULL
            MERGE (taster:Person {tasterName: record.taster_name})
                SET taster += {tasterTwitterHandle: record.taster_twitter_handle}
            MERGE (wine)-[:TASTED_BY]->(taster)
        WITH record, wine
            MERGE (country:Country {countryName: record.country})
            MERGE (wine)-[:IS_FROM_COUNTRY]->(country)
        WITH record, wine, country
        WHERE record.province IS NOT NULL
            MERGE (province:Province {provinceName: record.province})
            MERGE (wine)-[:IS_FROM_PROVINCE]->(province)
        WITH record, wine, country, province
            WHERE record.province IS NOT NULL AND record.country IS NOT NULL
            MERGE (province)-[:IS_LOCATED_IN]->(country)
        """
    tx.run(query, data=data)


def ingest_data(session: Session, validated_data: list[JsonBlob]) -> None:
    for data in validated_data:
        ids = [item["id"] for item in data]
        try:
            session.execute_write(build_query, data)
            print(f"Processed ids in range {min(ids)}-{max(ids)}")
        except Exception as e:
            print(f"{e}: Failed to ingest IDs in range {min(ids)}-{max(ids)}")


def main(data: list[JsonBlob]) -> None:
     with GraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
         with driver.session(database="neo4j") as session:
            # Create indexes and constraints
            create_indexes_and_constraints(session)
            # Ingest the data into Neo4j
            print("Validating data...")
            validated_data = validate(data, exclude_none=True)
            # Break the data into chunks
            chunked_data = chunk_iterable(validated_data, CHUNKSIZE)
            print("Ingesting data...")
            with Timer(name="ingest"):
                for chunk in chunked_data:
                    ids = [item["id"] for item in chunk]
                    try:
                        session.execute_write(build_query, chunk)
                        print(f"Processed ids in range {min(ids)}-{max(ids)}")
                    except Exception as e:
                        print(f"{e}: Failed to ingest IDs in range {min(ids)}-{max(ids)}")


if __name__ == "__main__":
    # fmt: off
    parser = argparse.ArgumentParser("Build a graph from the wine reviews JSONL data")
    parser.add_argument("--limit", type=int, default=0, help="Limit the size of the dataset to load for testing purposes")
    parser.add_argument("--chunksize", type=int, default=10_000, help="Size of each chunk to break the dataset into before processing")
    parser.add_argument("--filename", type=str, default="winemag-data-130k-v2.jsonl.gz", help="Name of the JSONL zip file to use")
    args = vars(parser.parse_args())
    # fmt: on

    LIMIT = args["limit"]
    DATA_DIR = Path(__file__).parents[2] / "data"
    FILENAME = args["filename"]
    CHUNKSIZE = args["chunksize"]

    # # Neo4j
    settings = get_settings()
    URI = f"bolt://{settings.neo4j_url}:7687"
    NEO4J_USER = settings.neo4j_user
    NEO4J_PASSWORD = settings.neo4j_password

    data = list(get_json_data(DATA_DIR, FILENAME))
    if LIMIT > 0:
        data = data[:LIMIT]

    if data:
        main(data)
        print("Finished execution!")