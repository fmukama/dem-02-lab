"""
preprocessing.py
================
STEP 2: clean and transform the raw movie data.

The TMDB API returns several nested / JSON-like fields (genres, cast,
production companies, ...). Here we:
  1. flatten those nested fields into simple pipe-separated text columns,
  2. fix data types and replace impossible values (0 budget, etc.),
  3. drop duplicates / bad rows and keep only released movies,
  4. reorder to the final schema the brief specifies.

The public entry point is `preprocess(df)`, which runs the whole pipeline.
"""

import ast # abstract syntax trees

import numpy as np
import pandas as pd


def _as_object(value):
    """
    Return a real Python object (list/dict) from a value that might already
    be an object OR a string like "[{'id': 28, 'name': 'Action'}]".

    Reason: straight from the API the fields are already parsed
    (lists/dicts), but after saving to and reloading from a CSV they come
    back as strings. Handling both keeps the pipeline robust either way.
    """
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return ast.literal_eval(value)  # safely parse the string
        except (ValueError, SyntaxError):
            return None
    return None


def _names(value, key="name", sep="|"):
    """
    Turn a list of dicts into one separated string of their `key` values.

    Example:
        [{'name': 'Action'}, {'name': 'Sci-Fi'}]  ->  "Action|Sci-Fi"
    Returns NaN when there is nothing to extract.
    """
    obj = _as_object(value)
    if not obj:
        return np.nan
    names = [d.get(key) for d in obj if isinstance(d, dict) and d.get(key)]
    return sep.join(names) if names else np.nan


def _collection_name(value):
    """Extract just the collection/franchise name (this field is a dict)."""
    obj = _as_object(value)
    if isinstance(obj, dict):
        return obj.get("name", np.nan)
    return np.nan


def _cast_names(credits, sep="|"):
    """All actor names joined by `sep` (e.g. 'Bruce Willis|Uma Thurman')."""
    obj = _as_object(credits)
    if not isinstance(obj, dict):
        return np.nan
    names = [c.get("name") for c in obj.get("cast", []) if c.get("name")]
    return sep.join(names) if names else np.nan


def _cast_size(credits):
    """How many actors are listed for the movie."""
    obj = _as_object(credits)
    return len(obj.get("cast", [])) if isinstance(obj, dict) else 0


def _director(credits, sep="|"):
    """Name(s) of the director(s) -- taken from crew where job == 'Director'."""
    obj = _as_object(credits)
    if not isinstance(obj, dict):
        return np.nan
    directors = [c.get("name") for c in obj.get("crew", [])
                 if c.get("job") == "Director"]
    return sep.join(directors) if directors else np.nan


def _crew_size(credits):
    """How many crew members are listed for the movie."""
    obj = _as_object(credits)
    return len(obj.get("crew", [])) if isinstance(obj, dict) else 0


# Task 2.1 - 2.3 : drop junk columns and flatten the JSON-like columns
DROP_COLUMNS = ["adult", "imdb_id", "original_title", "video", "homepage"]


def flatten_columns(df):
    """
    Drop irrelevant columns and convert every nested field into a clean
    text column: genres, collection, languages, countries, companies,
    cast, director, plus cast_size / crew_size.
    """
    df = df.copy()

    # 1) drop columns we will never use in the analysis
    df = df.drop(columns=[c for c in DROP_COLUMNS if c in df.columns])

    # 2) flatten the list/dict columns into pipe-separated strings
    df["genres"] = df["genres"].apply(_names)
    df["belongs_to_collection"] = df["belongs_to_collection"].apply(_collection_name)
    df["spoken_languages"] = df["spoken_languages"].apply(
        lambda v: _names(v, key="english_name")  # readable English name
    )
    df["production_countries"] = df["production_countries"].apply(_names)
    df["production_companies"] = df["production_companies"].apply(_names)

    # 3) pull cast & crew details out of the nested `credits` field
    df["cast"] = df["credits"].apply(_cast_names)
    df["cast_size"] = df["credits"].apply(_cast_size)
    df["director"] = df["credits"].apply(_director)
    df["crew_size"] = df["credits"].apply(_crew_size)
    df = df.drop(columns=["credits"])  # no longer needed once flattened

    return df


# Task 2.5 - 2.6 : data types, unrealistic values, unit conversion

def fix_dtypes_and_values(df):
    """
    Convert data types, replace impossible values with NaN and express
    money in millions of USD (easier to read than raw dollars).
    """
    df = df.copy()

    # numeric conversions -- invalid text becomes NaN instead of crashing
    for col in ["budget", "id", "popularity"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # release_date -> a real datetime so we can group by year later
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    # A budget / revenue / runtime of 0 is not real data -> mark as missing
    for col in ["budget", "revenue", "runtime"]:
        if col in df.columns:
            df[col] = df[col].replace(0, np.nan)

    # Convert money to millions of USD (budget_musd, revenue_musd)
    df["budget_musd"] = df["budget"] / 1_000_000
    df["revenue_musd"] = df["revenue"] / 1_000_000

    # A movie with 0 votes has a meaningless 0.0 average rating -> NaN
    df.loc[df["vote_count"] == 0, "vote_average"] = np.nan

    # Replace known placeholder text with NaN
    placeholders = ["No Data", "No overview found.", ""]
    for col in ["overview", "tagline"]:
        if col in df.columns:
            df[col] = df[col].replace(placeholders, np.nan)

    return df


# Task 2.7 - 2.11 : row-level cleaning, filtering, reorder, reset index

# The exact final column order requested in the brief.
FINAL_COLUMN_ORDER = [
    "id", "title", "tagline", "release_date", "genres", "belongs_to_collection",
    "original_language", "budget_musd", "revenue_musd", "production_companies",
    "production_countries", "vote_count", "vote_average", "popularity", "runtime",
    "overview", "spoken_languages", "poster_path", "cast", "cast_size",
    "director", "crew_size",
]


def clean_rows(df):
    """
    Remove duplicates and bad rows, keep only well-populated released
    movies, then reorder to the final schema and reset the index.
    """
    df = df.copy()

    # Task 2.7 -- drop duplicate movies and any row with no id or title.
    # NOTE: we deduplicate on "id" (the unique movie key) instead of the whole
    # row. A plain df.drop_duplicates() tries to hash every column, but some
    # raw columns (e.g. TMDB's newer 'origin_country') still hold Python lists
    # at this point, and lists are unhashable -> "unhashable type: 'list'".
    df = df.dropna(subset=["id", "title"])
    df = df.drop_duplicates(subset=["id"])

    # Task 2.8 -- keep only rows that have at least 10 non-NaN values
    df = df.dropna(thresh=10)

    # Task 2.9 -- keep only 'Released' movies, then drop the status column
    if "status" in df.columns:
        df = df[df["status"] == "Released"].copy()
        df = df.drop(columns=["status"])

    # Task 2.10 -- reorder to the exact layout the brief asks for
    ordered = [c for c in FINAL_COLUMN_ORDER if c in df.columns]
    df = df[ordered]

    # Task 2.11 -- clean id type and reset the index
    df["id"] = df["id"].astype("int64")
    df = df.reset_index(drop=True)

    return df


# Public entry point -- run the whole cleaning pipeline in order

def preprocess(df):
    """Run flatten -> fix dtypes/values -> clean rows, and return the result."""
    df = flatten_columns(df)
    df = fix_dtypes_and_values(df)
    df = clean_rows(df)
    print(f"Clean dataset: {df.shape[0]} movies x {df.shape[1]} columns.")
    return df