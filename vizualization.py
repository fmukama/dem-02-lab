"""
visualization.py
=================
STEP 4: visual summaries of the cleaned dataset.
"""

import matplotlib.pyplot as plt

import analysis  # reuse add_metrics / franchise_vs_standalone


def _new_ax(ax, figsize):
    """Create a fresh Axes if the caller didn't pass one in.
    It prevents errors by automatically generating a new canvas if the user forgets to provide one.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
    return ax



# 1) Revenue vs Budget

def revenue_vs_budget(df, ax=None):
    """
    Scatter of revenue against budget, with a dashed break-even line
    (points above the line made money, points below lost money).
    """
    ax = _new_ax(ax, (8, 6))
    ax.scatter(df["budget_musd"], df["revenue_musd"], alpha=0.7, edgecolor="k")

    # break-even line: revenue == budget
    top = max(df["budget_musd"].max(), df["revenue_musd"].max())
    ax.plot([0, top], [0, top], "r--", label="Break-even (revenue = budget)")

    ax.set_xlabel("Budget (million USD)")
    ax.set_ylabel("Revenue (million USD)")
    ax.set_title("Revenue vs Budget")
    ax.legend()
    return ax

# 2) ROI distribution by genre

def roi_by_genre(df, ax=None):
    """
    Median ROI per genre. Because a movie can have several genres (joined by
    '|'), we split and explode so each genre is counted separately.
    """
    data = analysis.add_metrics(df).dropna(subset=["genres", "roi"]).copy()
    data["genres"] = data["genres"].str.split("|")
    exploded = data.explode("genres")

    median_roi = exploded.groupby("genres")["roi"].median().sort_values()

    ax = _new_ax(ax, (9, 6))
    median_roi.plot(kind="barh", ax=ax, color="teal")
    ax.set_xlabel("Median ROI (revenue / budget)")
    ax.set_ylabel("Genre")
    ax.set_title("ROI Distribution by Genre (median)")
    return ax

# 3) Popularity vs Rating

def popularity_vs_rating(df, ax=None):
    """Scatter of popularity against average rating."""
    ax = _new_ax(ax, (8, 6))
    ax.scatter(df["vote_average"], df["popularity"], alpha=0.7,
               color="darkorange", edgecolor="k")
    ax.set_xlabel("Average Rating")
    ax.set_ylabel("Popularity")
    ax.set_title("Popularity vs Rating")
    return ax