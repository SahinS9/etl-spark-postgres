import requests
from pprint import pprint
from .config import POSTS_URL, USERS_URL, COMMENTS_URL


def inspect_posts_api() -> None:
    response = requests.get(POSTS_URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    print("Type of reponse:", type(data))
    print("Number of records:", len(data))
    print("\nKeys in tfirst record:")
    pprint(data[0].keys())

    print("\nFull first record:")
    pprint(data[0])


def inspect_users_api() -> None:
    response = requests.get(USERS_URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    print("Type of reponse:", type(data))
    print("Number of records:", len(data))
    print("\nKeys in tfirst record:")
    pprint(data[0].keys())

    print("\nFull first record:")
    pprint(data[0])


def inspect_comments_api() -> None:
    response = requests.get(COMMENTS_URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    print("Type of reponse:", type(data))
    print("Number of records:", len(data))
    print("\nKeys in tfirst record:")
    pprint(data[0].keys())

    print("\nFull first record:")
    pprint(data[0])


if __name__ == "__main__":
    # inspect_users_api()
    # inspect_comments_api()
    inspect_posts_api()