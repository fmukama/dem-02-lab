"""
ingestion.py
============
STEP 1: fetch raw movie data from the TMDB API.

Key idea
--------
For each movie we call the "movie details" endpoint with
`append_to_response=credits`. That single call returns BOTH the movie
details (budget, revenue, genres, ...) AND its cast & crew, which saves us
a second request per movie. All movies are collected into one DataFrame.

Endpoint used:
    GET /3/movie/{movie_id}?append_to_response=credits
Docs:
    https://developer.themoviedb.org/reference/movie-details
"""

import time

import pandas as pd
import requests

import config


def fetch_movie(movie_id, session=None):
    """
    Fetch a single movie (details + credits) from TMDB.

    Parameters
    ----------
    movie_id : int
        The TMDB id of the movie.
        session : requests.Session, optional
        A re-used session makes repeated calls faster (keeps the
        connection open). If None, a plain requests.get is used.

    Returns
    -------
    dict or None
        The parsed JSON for the movie, or None when the id is invalid
        (e.g. 0) or the request failed for any reason.
    """
    url = f"{config.BASE_URL}/movie/{movie_id}"
    params = {"append_to_response": "credits"}

    # Use the session's .get if we were given one, else the module-level get.
    getter = session.get if session is not None else requests.get
    response = getter(url, headers=config.HEADERS, params=params)

    # A valid movie returns HTTP 200. Anything else (404 for id 0, 401 for a
    # bad token, 429 if rate-limited) means we skip this id.
    if response.status_code != 200:
        print(f"  ! Skipping id {movie_id} (HTTP {response.status_code})")
        return None

    return response.json()


def fetch_movies(movie_ids=None, pause=0.25):
    """
    Fetch many movies and return them as a single raw DataFrame.

    Parameters
    ----------
    movie_ids : list of int, optional
        Which movies to fetch. Defaults to config.MOVIE_IDS (the brief's list).
    pause : float
        Seconds to wait between calls so we stay polite / under the rate limit.

    Returns
    -------
    pandas.DataFrame
        One row per successfully fetched movie. The nested fields
        (genres, credits, production_companies, ...) are still Python
        objects at this stage -- preprocessing.py turns them into clean
        columns.
    """
    if movie_ids is None:
        movie_ids = config.MOVIE_IDS

    records = []
    # A single Session is reused for every request (faster than reconnecting).
    with requests.Session() as session:
        for movie_id in movie_ids:
            data = fetch_movie(movie_id, session=session)
            if data is not None:
                records.append(data)
                print(f"  ok  Fetched '{data.get('title')}' (id {movie_id})")
            time.sleep(pause)  # small delay between calls

    df = pd.DataFrame(records)
    print(f"\nFetched {len(df)} movies with {df.shape[1]} raw columns.")
    return df


def save_raw(df, path="movies_raw.csv"):
    """Save the raw DataFrame to CSV as a backup so you don't re-hit the API."""
    df.to_csv(path, index=False)
    print(f"Raw data saved to {path}")


def load_raw(path="movies_raw.csv"):
    """
    Reload a previously saved raw DataFrame from CSV.
    """
    return pd.read_csv(path)