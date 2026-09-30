"""Regenerate the scorecard figure from the exported aggregates.

Reads data/exports/fct_monthly_quality.csv (written by export_bi.py) and
writes docs/img/completeness-by-month.png. Aggregates only. matplotlib
is not a project dependency - run it on demand:

    uv run --with matplotlib python scripts/make_figure.py
"""

import csv
from datetime import date
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SOURCE = Path("data/exports/fct_monthly_quality.csv")
TARGET = Path("docs/img/completeness-by-month.png")
CUT = date(2024, 10, 1)
BLUE, ORANGE = "#2a78d6", "#eb6834"
TXT, TXT2, GRID = "#0b0b0b", "#52514e", "#e8e7e3"


def main() -> None:
    rows = []
    with open(SOURCE, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            month = date.fromisoformat(row["mois_deces"])
            if date(2020, 1, 1) <= month <= date(2026, 6, 1):
                n = int(row["n_deces"])
                rows.append(
                    (
                        month,
                        100 * int(row["n_connus_30_jours"]) / n,
                        100 * int(row["n_connus_90_jours"]) / n,
                    )
                )
    rows.sort()
    months = [r[0] for r in rows]
    p30 = [r[1] for r in rows]
    p90 = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(9.6, 4.8), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    ax.plot(
        months,
        p90,
        color=BLUE,
        lw=2,
        solid_capstyle="round",
        label="known within 90 days",
    )
    ax.plot(
        months,
        p30,
        color=ORANGE,
        lw=2,
        solid_capstyle="round",
        label="known within 30 days",
    )
    ax.axvline(CUT, color=TXT2, lw=1, ls=(0, (4, 3)), alpha=0.7)
    ax.axvspan(date(2020, 1, 1), CUT, color="#000000", alpha=0.03, lw=0)
    ax.text(
        date(2022, 6, 1),
        22,
        "archive era - monthlies deleted after consolidation,\n"
        "only the annual files remain; the spikes are late-year\n"
        "deaths caught by the January annual release",
        ha="center",
        va="center",
        fontsize=8.8,
        color=TXT2,
        linespacing=1.55,
    )
    ax.text(
        date(2026, 2, 1),
        30,
        "observable window\nsurviving monthly increments\nmeasure the real process",
        ha="center",
        va="center",
        fontsize=8.8,
        color=TXT2,
        linespacing=1.55,
    )
    ax.annotate(
        "known within 90 days\nwindow avg 99.2%",
        xy=(months[-1], p90[-1]),
        xytext=(8, 2),
        textcoords="offset points",
        va="center",
        fontsize=9.5,
        color=BLUE,
        fontweight="bold",
        linespacing=1.4,
    )
    ax.annotate(
        "known within 30 days\nwindow avg 60.2%",
        xy=(months[-1], p30[-1]),
        xytext=(8, -2),
        textcoords="offset points",
        va="center",
        fontsize=9.5,
        color=ORANGE,
        fontweight="bold",
        linespacing=1.4,
    )
    ax.annotate(
        "Oct 2024",
        xy=(CUT, 103),
        xytext=(0, 3),
        textcoords="offset points",
        ha="center",
        fontsize=8.5,
        color=TXT2,
    )
    ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=8.5,
        handlelength=1.6,
        borderaxespad=0.2,
        labelcolor=TXT2,
    )
    ax.set_ylim(0, 108)
    ax.set_yticks(range(0, 101, 25))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_xlim(date(2020, 1, 1), date(2027, 8, 1))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=TXT2, length=0)
    ax.set_title(
        "Share of each month's deaths present in the public register, by death month",
        loc="left",
        fontsize=12,
        color=TXT,
        pad=14,
        fontweight="bold",
    )
    fig.text(
        0.002,
        0.015,
        "Source - fct_monthly_quality (29.1M canonical deaths);"
        " reproduce with dbt/analyses/headline_completeness.sql",
        fontsize=7.5,
        color=TXT2,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(TARGET, facecolor="#fcfcfb")
    print(f"{TARGET} written from {len(rows)} months")


if __name__ == "__main__":
    main()
