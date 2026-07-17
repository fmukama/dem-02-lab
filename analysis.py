"""
analysis.py
===========
STEP 3: KPIs, rankings, searches and group analysis.

Contents
--------
1. add_metrics(df)-> adds derived columns: profit_musd, roi
2. rank_movies(...)-> the required User-Defined Function (UDF) that powers every "best / worst" ranking
3. thin wrappers-> highest_revenue, highest_roi, ... (10 KPIs)
4. search functions-> the two required search queries
5. group analysis-> franchise vs standalone, top franchises, top directors

Money columns are already in millions of USD.
"""

# Derived metrics used across the rankings

def add_metrics(df):
    """
    Add the two derived KPI columns the rankings need:
        profit_musd = revenue_musd - budget_musd
        roi         = revenue_musd / budget_musd   (Return On Investment)
    ROI is left as NaN when budget is missing (can't divide by NaN/0).
    """
    df = df.copy()
    df["profit_musd"] = df["revenue_musd"] - df["budget_musd"]
    df["roi"] = df["revenue_musd"] / df["budget_musd"]
    return df


# Task 3.1 : the ranking UDF (one function drives all 10 rankings)

def rank_movies(df, by, ascending=False, n=5,
                min_budget=None, min_votes=None, extra_cols=None):
    """
    Generic ranking helper -- the project's required UDF.

    Parameters
    ----------
    by : str
        Column to sort by. Can be a normal column ('revenue_musd',
        'budget_musd', 'vote_count', 'vote_average', 'popularity') or one
        of the derived metrics 'profit_musd' / 'roi'.
    ascending : bool
        False -> highest first (best). True -> lowest first (worst).
    n : int
        How many movies to return.
    min_budget : float, optional
        Keep only movies with budget_musd >= this (used for ROI rankings,
        where tiny budgets create meaningless huge ratios).
    min_votes : int, optional
        Keep only movies with vote_count >= this (used for rating rankings).
    extra_cols : list of str, optional
        Extra columns to show next to the ranking metric.

    Returns
    -------
    pandas.DataFrame
        A tidy table: title + the ranking metric (+ any extra columns).
    """
    data = add_metrics(df)

    # optional quality filters
    if min_budget is not None:
        data = data[data["budget_musd"] >= min_budget]
    if min_votes is not None:
        data = data[data["vote_count"] >= min_votes]

    # only rank rows where the sort column actually has a value
    data = data.dropna(subset=[by])

    ranked = data.sort_values(by=by, ascending=ascending).head(n)

    cols = ["title", by]
    if extra_cols:
        cols += [c for c in extra_cols if c not in cols]
    return ranked[cols].reset_index(drop=True)


# --- Task 3.1 wrappers: the 10 required "best / worst" rankings
def highest_revenue(df, n=5):
    """Top movies by revenue."""
    return rank_movies(df, "revenue_musd", n=n)


def highest_budget(df, n=5):
    """Top movies by budget."""
    return rank_movies(df, "budget_musd", n=n)


def highest_profit(df, n=5):
    """Top movies by profit (revenue - budget)."""
    return rank_movies(df, "profit_musd", n=n, extra_cols=["revenue_musd", "budget_musd"])


def lowest_profit(df, n=5):
    """Biggest money-losers (lowest profit)."""
    return rank_movies(df, "profit_musd", ascending=True, n=n,
                       extra_cols=["revenue_musd", "budget_musd"])


def highest_roi(df, n=5):
    """Best ROI -- only movies with budget >= 10M (avoids tiny-budget noise)."""
    return rank_movies(df, "roi", n=n, min_budget=10,
                       extra_cols=["revenue_musd", "budget_musd"])


def lowest_roi(df, n=5):
    """Worst ROI -- only movies with budget >= 10M."""
    return rank_movies(df, "roi", ascending=True, n=n, min_budget=10,
                       extra_cols=["revenue_musd", "budget_musd"])


def most_voted(df, n=5):
    """Movies with the most votes."""
    return rank_movies(df, "vote_count", n=n)


def highest_rated(df, n=5):
    """Highest rated -- only movies with at least 10 votes."""
    return rank_movies(df, "vote_average", n=n, min_votes=10, extra_cols=["vote_count"])


def lowest_rated(df, n=5):
    """Lowest rated -- only movies with at least 10 votes."""
    return rank_movies(df, "vote_average", ascending=True, n=n, min_votes=10, extra_cols=["vote_count"])


def most_popular(df, n=5):
    """Most popular movies (TMDB popularity score)."""
    return rank_movies(df, "popularity", n=n)


# Task 3.2 : advanced search queries

def search_movies(df, genres=None, cast=None, director=None,                sort_by="vote_average", ascending=False):
    """
    Flexible search over the cleaned dataset.

    genres / cast / director are matched as case-insensitive substrings, so
    'Bruce Willis' matches inside the pipe-joined cast string. `genres` may
    be a single string or a list of strings (ALL must be present).

    Returns the matching rows sorted by `sort_by`.
    """
    data = df.copy()

    if genres:
        # allow a single genre string or a list of genres (AND logic)
        genre_list = [genres] if isinstance(genres, str) else genres
        for g in genre_list:
            # na: # Keeps the filter from breaking if missing values exist
            data = data[data["genres"].str.contains(g, case=False, na=False)]
    if cast:
        data = data[data["cast"].str.contains(cast, case=False, na=False)]
    if director:
        data = data[data["director"].str.contains(director, case=False, na=False)]

    return data.sort_values(by=sort_by, ascending=ascending)


def search_scifi_action_bruce_willis(df):
    """
    Search 1: best-rated Science-Fiction Action movies starring Bruce Willis,
    sorted by rating (highest to lowest).
    """
    result = search_movies(
        df,
        genres=["Science Fiction", "Action"],
        cast="Bruce Willis",
        sort_by="vote_average",
        ascending=False,
    )
    return result[["title", "vote_average", "genres", "cast"]].reset_index(drop=True)


def search_thurman_tarantino(df):
    """
    Search 2: movies starring Uma Thurman directed by Quentin Tarantino,
    sorted by runtime (shortest to longest).
    """
    result = search_movies(
        df,
        cast="Uma Thurman",
        director="Quentin Tarantino",
        sort_by="runtime",
        ascending=True,
    )
    return result[["title", "runtime", "director", "cast"]].reset_index(drop=True)

# Task 3.3 : franchise vs standalone comparison

def franchise_vs_standalone(df):
    """
    Compare franchise movies (belongs_to_collection is set) against
    standalone movies across the KPIs the brief lists.

    Returns a 2-row table indexed by 'Franchise' / 'Standalone'.
    """
    data = add_metrics(df)
    data["is_franchise"] = data["belongs_to_collection"].notna() # Rows are flagged as True if they belong to a collection, and False if they do not.

    summary = data.groupby("is_franchise").agg(
        mean_revenue=("revenue_musd", "mean"),
        median_roi=("roi", "median"),
        mean_budget=("budget_musd", "mean"),
        mean_popularity=("popularity", "mean"),
        mean_rating=("vote_average", "mean"),

        #  The dataset is split into two groups to calculate the metrics for each group.
    )

    # rename the True/False index into readable labels
    summary.index = summary.index.map({True: "Franchise", False: "Standalone"})
    return summary

