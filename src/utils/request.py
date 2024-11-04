import requests

def fetch_url(url: str) -> dict:
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
    # Parse the HTML content
        return response.json()
    else:
        raise Exception(f"Failed to retrieve the webpage. Status code: {response.status_code}")