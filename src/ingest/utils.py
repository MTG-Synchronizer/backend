from functools import lru_cache
import requests
from dotenv import load_dotenv
from config.settings import Settings
from typing import Iterator

# --- Blocking functions ---



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


def fetch_url(url: str) -> dict:
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
    # Parse the HTML content
        return response.json()
    else:
        raise Exception(f"Failed to retrieve the webpage. Status code: {response.status_code}")