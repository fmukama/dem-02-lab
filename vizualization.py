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
