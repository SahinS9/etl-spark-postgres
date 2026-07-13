from __future__ import annotations

import os
from typing import Any
from pathlib import Path
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

PROJECT_ROOT= Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env", override=False)

DATABASE_URL: str | None = os.getenv("DATABASE_URL")

API_BASE_URL: str | None = os.getenv("API_BASE_URL")
API_KEY: str | None = os.getenv("API_KEY")  # no key for this API


HTTP_TIMEOUT_SECONDS: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
USER_AGENT: str = os.getenv("USER_AGENT", "etl-miniproject/1.0")


def validate_config() -> None:
     missing: list[str] = []

     if not DATABASE_URL:
          missing.append("DATABASE_URL")
     if not API_BASE_URL:
          missing.append("API_BASE_URL")
     if missing:
          raise RuntimeError(f"Missing required configuration: {','.join(missing)}")

     if HTTP_TIMEOUT_SECONDS <= 0:
          raise RuntimeError(
               "HTTP_TIMEOUT_SECONDS must be greater than zero"
          )


def endpoint(path: str) -> list[dict[str, Any]]:
     if not API_BASE_URL:
          raise RuntimeError("API_BASE_URL is not configured")
     
     clean_base_url = API_BASE_URL.rstrip("/") + "/"
     clean_path = path.lstrip("/")

     return urljoin(clean_base_url, clean_path)


def posts_url() -> str: return endpoint("posts")
def users_url() -> str: return endpoint("users")
def comments_url() -> str: return endpoint("comments")


def fetch_json(url: str) -> list[dict[str, Any]]:
    headers = {"User-Agent": USER_AGENT,
               "Accept": "application/json"}

    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    try:
         response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS, headers=headers)
    except requests.exceptions.Timeout as exc:
         raise RuntimeError (f"API request timed out after {HTTP_TIMEOUT_SECONDS} seconds: {url}") from exc
    except requests.exceptions.ConnectionError as exc:
         raise RuntimeError(f"Failed to connect to API endpoint: {url}") from exc
    except requests.exceptions.RequestException as exc:
         raise RuntimeError(f"API request failed: {url}") from exc
    
    if not response.ok:
         response_preview = response.text[:500]
         raise RuntimeError(f"API returned HTTP {response.status_code} for {url}: {response_preview.text}")
    
    try:
         payload = response.json()
    except ValueError as exc:
         raise RuntimeError(f"API response is not valid JSON: {url}") from exc
    
    if not isinstance(payload, list):
         raise RuntimeError(f"API response has unexpected type: {type(payload).__name__}")
    
    if not payload:
         raise RuntimeError(f"API returened an empty dataset: {url}")
    
    if not all(isinstance(item, dict) for item in payload):
         raise RuntimeError("API response must be a list of JSON objects")
    
    return payload