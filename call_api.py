# Boilerplate code since we will call the api a lot
# Expects url to call and data format to return in
from typing import Optional
import requests
def call_api(token: str, url: str, return_format: Optional[dict] = None) -> dict:
    """Call the API with the given token and URL, returning the response data.

    Args:
        token (str): Login token
        url (str): API endpoint URL
        return_format (dict): Expected format of the response data. If not specified, returns json response.

    Raises:
        Exception: If there is an error calling the API.

    Returns:
        dict: The response data in the expected format.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"kkstrauth={token};",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if return_format:
            return {key: data.get(key) for key in return_format}
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error calling API: {e}")