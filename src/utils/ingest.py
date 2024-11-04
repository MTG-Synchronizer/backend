from functools import lru_cache
from dotenv import load_dotenv
from config.settings import Settings
from typing import Iterator

@lru_cache()
def get_settings():
    load_dotenv()
    # Use lru_cache to avoid loading .env file for every request
    return Settings()

def chunk_iterable(item_list: list, chunksize: int) -> Iterator[list]:
    """
    Break a large iterable into an iterable of smaller iterables of size `chunksize`
    """
    for i in range(0, len(item_list), chunksize):
        yield item_list[i : i + chunksize]