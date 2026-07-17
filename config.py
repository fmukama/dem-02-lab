import os

from dotenv import load_dotenv
load_dotenv()

TMDB_BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN")

BASE_URL = "https://api.themoviedb.org/3"   # from https://developer.themoviedb.org/reference/getting-started

# The header sent with every request. TMDB's v4 auth expects the token
# in the standard "Authorization: Bearer <token>" form.
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_BEARER_TOKEN}",
}

MOVIE_IDS = [
    0, 299534, 19995, 140607, 299536, 597, 135397,
    420818, 24428, 168259, 99861, 284054, 12445,
    181808, 330457, 351286, 109445, 321612, 260513,
]


def check_token() -> bool:
    """Small helper so the notebook can confirm the token was loaded."""
    if not TMDB_BEARER_TOKEN:
        print("No Bearer token found.")
        return False
    print("TMDB token loaded successfully.")
    return True