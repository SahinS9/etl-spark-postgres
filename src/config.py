import os
from typing import Any

from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


PROJECT_ROOT= Path(__file__).resolve().parent.parent

DATABASE_URL: str | None = os.getenv("DATABASE_URL")

API_BASE_URL: str = os.getenv("API_BASE_URL", "https://jsonplaceholder.typicode.com")
API_KEY: str | None = os.getenv("API_KEY")  # no key for this API


HTTP_TIMEOUT_SECONDS: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
USER_AGENT: str = os.getenv("USER_AGENT", "etl-miniproject/1.0")

# Endpoints 
POSTS_URL: str = f"{API_BASE_URL}/posts"
USERS_URL: str = f"{API_BASE_URL}/users"
COMMENTS_URL: str = f"{API_BASE_URL}/comments"


def validate_config() -> None:
     if not DATABASE_URL:
          raise RuntimeError("DATABASE_URL is not set in .env")
     if not API_BASE_URL:
          raise RuntimeError("API_BASE_URL is not set in .env")





def fetch_json(url: str) -> list[dict[str, Any]]:
    headers = {"User-Agent": USER_AGENT}

    if API_KEY:
        headers["Authorization"] = f"Bearerwh {API_KEY}"
    
    try:
         response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS, headers=headers)
    except requests.exceptions.Timeout as exc:
         raise RuntimeError (f"API request timed out after {HTTP_TIMEOUT_SECONDS} seconds") from exc
    except requests.exceptions.ConnectionError as exc:
         raise RuntimeError(f"Failed to connect to API endpoint") from exc
    
    if not response.ok:
         raise RuntimeError(f"API returned HTTP {response.status_code}: {response.text}")
    
    try:
         payload = response.json()
    except ValueError as exc:
         raise RuntimeError("API response is not valid JSON") from exc
    
    if not isinstance(payload, list):
         raise RuntimeError(f"API response has unexpected type: {type(payload)}")
    
    if len(payload)==0:
         raise RuntimeError("API returened an empty dataset")
    
    return payload