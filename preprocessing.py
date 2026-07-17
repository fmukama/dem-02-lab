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

