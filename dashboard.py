# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair>=6.0.0",
#     "marimo>=0.22.4",
#     "polars>=1.39.3",
# ]
# ///
import marimo

app = marimo.App(width="full", app_title="Pixie Chess Analytics")


@app.cell
def __():
    import marimo as mo
    import altair as alt
    import polars as pl

    # Hide Altair's chart action menu (View Source / Open in Vega Editor / …).
    _ = alt.renderers.set_embed_options(actions=False)
    return alt, mo, pl


@app.cell
def __(mo):
    mo.md(
        """
        # Pixie Chess Analytics

        Interactive dashboard for [Pixie Chess](https://www.pixiechess.xyz/) analytics.
        """
    )
    return


@app.cell
def __(mo, pl):
    import math
    import json
    import urllib.request
    from pathlib import Path

    _loc = mo.notebook_location() / "data" / "players.jsonl"
    if isinstance(_loc, Path):
        with open(_loc) as _f:
            _rows = [json.loads(_line) for _line in _f if _line.strip()]
    else:
        with urllib.request.urlopen(str(_loc)) as _f:
            _rows = [json.loads(_line) for _line in _f if _line.strip()]
    players = pl.DataFrame(_rows)
    INITIAL_RATING = 1500

    _rmin = int(players["rating"].min())
    _rmax = int(players["rating"].max())
    RATING_MIN = (_rmin // 100) * 100
    RATING_MAX = ((_rmax // 100) + 1) * 100
    RATING_TICKS = list(range(RATING_MIN, RATING_MAX + 1, 100))

    _gmax = int(players["games_played"].max())
    _top = 10 ** math.ceil(math.log10(max(_gmax, 1)))
    GAMES_TICKS = [10 ** k for k in range(0, int(math.log10(_top)) + 1)]
    GAMES_MAX = _top
    return (
        GAMES_MAX,
        GAMES_TICKS,
        INITIAL_RATING,
        RATING_MAX,
        RATING_MIN,
        RATING_TICKS,
        players,
    )


@app.cell
def __(mo, players):
    mo.md(
        f"""
        ## Overview

        - **Players:** {players.height:,}
        - **Games played:** {players['games_played'].sum() // 2:,}
        - **Mean rating:** {players['rating'].mean():,.1f}
        - **Median rating:** {players['rating'].median():,.1f}
        - **Min rating:** {players['rating'].min():,.1f}
        - **Max rating:** {players['rating'].max():,.1f}
        - **Mean games played:** {players['games_played'].mean():.1f}
        - **Median games played:** {players['games_played'].median():.1f}
        - **Max games played:** {players['games_played'].max():,}
        """
    )
    return


@app.cell
def __(mo):
    mo.md("## Rating Distribution")
    return


@app.cell
def __(INITIAL_RATING, RATING_MAX, RATING_MIN, RATING_TICKS, alt, players):
    _mean = players["rating"].mean()
    _median = players["rating"].median()

    _hist = (
        alt.Chart(players)
        .mark_bar(opacity=0.75)
        .encode(
            x=alt.X(
                "rating:Q",
                bin=alt.Bin(step=10, extent=[RATING_MIN, RATING_MAX]),
                title="rating",
                scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
                axis=alt.Axis(
                    values=RATING_TICKS,
                    format="d",
                    labelAngle=0,
                    grid=True,
                    domainWidth=1,
                    tickWidth=1,
                ),
            ),
            y=alt.Y(
                "count():Q",
                title="players",
                axis=alt.Axis(
                    format="d",
                    tickMinStep=1,
                    grid=True,
                    domainWidth=1,
                    tickWidth=1,
                ),
            ),
            tooltip=[alt.Tooltip("count():Q", title="players")],
        )
    )

    _initial_lbl = f"initial: {INITIAL_RATING}"
    _mean_lbl = f"mean: {_mean:.1f}"
    _median_lbl = f"median: {_median:.1f}"
    _rules = (
        alt.Chart(
            alt.InlineData(
                values=[
                    {"value": INITIAL_RATING, "label": _initial_lbl, "name": "initial"},
                    {"value": _mean, "label": _mean_lbl, "name": "mean"},
                    {"value": _median, "label": _median_lbl, "name": "median"},
                ]
            )
        )
        .mark_rule(strokeDash=[4, 4], size=2)
        .encode(
            x="value:Q",
            color=alt.Color(
                "label:N",
                title=None,
                scale=alt.Scale(
                    domain=[_initial_lbl, _mean_lbl, _median_lbl],
                    range=["#7f7f7f", "#d62728", "#9467bd"],
                ),
            ),
            tooltip=[
                alt.Tooltip("name:N", title="label"),
                alt.Tooltip("value:Q", format=",.1f", title="value"),
            ],
        )
    )

    rating_chart = (
        (_hist + _rules)
        .properties(
            height=420, width="container", title="Pixie Chess: Rating Distribution"
        )
        .interactive(bind_y=False)
    )
    rating_chart
    return (rating_chart,)


@app.cell
def __(mo):
    mo.md("## Games Played Distribution")
    return


@app.cell
def __(mo):
    games_log_y = mo.ui.switch(value=False, label="log y-axis")
    games_log_y
    return (games_log_y,)


@app.cell
def __(alt, games_log_y, players):
    _max = int(players["games_played"].max())
    _step = max(1, (_max // 60))  # ~60 bins
    _domain_max = ((_max // _step) + 1) * _step
    _mean = float(players["games_played"].mean())
    _median = float(players["games_played"].median())

    _hist = (
        alt.Chart(players)
        .mark_bar(opacity=0.75)
        .encode(
            x=alt.X(
                "games_played:Q",
                bin=alt.Bin(step=_step, extent=[0, _domain_max]),
                title="games played (g)",
                scale=alt.Scale(domain=[0, _domain_max], nice=False),
                axis=alt.Axis(
                    format="d",
                    labelAngle=0,
                    tickMinStep=1,
                    grid=True,
                    domainWidth=1,
                    tickWidth=1,
                ),
            ),
            y=alt.Y(
                "count():Q",
                title="players" + (" (log)" if games_log_y.value else ""),
                scale=alt.Scale(
                    type="log" if games_log_y.value else "linear",
                    base=10,
                ),
                axis=alt.Axis(
                    format="d",
                    tickMinStep=1,
                    grid=True,
                    domainWidth=1,
                    tickWidth=1,
                ),
            ),
            tooltip=[alt.Tooltip("count():Q", title="players")],
        )
    )

    _mean_lbl = f"mean: {_mean:.1f}"
    _median_lbl = f"median: {_median:.1f}"
    _rules = (
        alt.Chart(
            alt.InlineData(
                values=[
                    {"value": _mean, "label": _mean_lbl, "name": "mean"},
                    {"value": _median, "label": _median_lbl, "name": "median"},
                ]
            )
        )
        .mark_rule(strokeDash=[4, 4], size=2)
        .encode(
            x="value:Q",
            color=alt.Color(
                "label:N",
                title=None,
                scale=alt.Scale(
                    domain=[_mean_lbl, _median_lbl],
                    range=["#d62728", "#9467bd"],
                ),
            ),
            tooltip=[
                alt.Tooltip("name:N", title="label"),
                alt.Tooltip("value:Q", format=",.1f", title="value"),
            ],
        )
    )

    games_chart = (
        (_hist + _rules)
        .properties(
            height=420, width="container", title="Pixie Chess: Games Played Distribution"
        )
        .interactive(bind_y=False)
    )
    games_chart
    return (games_chart,)


@app.cell
def __(pl, players):
    # Bucket games played: [1], [2-4], [5-16], [17-64], ...
    _max_games = players["games_played"].max()
    _buckets = []
    _lo, _hi = 1, 1
    while _lo <= _max_games:
        label = f"g = {_lo}" if _lo == _hi else f"g ∈ [{_lo}, {_hi}]"
        _buckets.append((label, _lo, _hi))
        _lo = _hi + 1
        _hi = _hi * 4 if _hi > 1 else 4

    players_bucketed = players.with_columns(
        pl.coalesce(
            [
                pl.when(
                    (pl.col("games_played") >= lo) & (pl.col("games_played") <= hi)
                )
                .then(pl.lit(label))
                .otherwise(None)
                for label, lo, hi in _buckets
            ]
        ).alias("games_bucket")
    ).drop_nulls("games_bucket")

    bucket_order = [label for label, _, _ in _buckets]
    return bucket_order, players_bucketed


@app.cell
def __(mo):
    mo.md("## Rating Boxplots by Games Played")
    return


@app.cell
def __(
    RATING_MAX,
    RATING_MIN,
    RATING_TICKS,
    alt,
    bucket_order,
    pl,
    players,
    players_bucketed,
):
    # Compute box stats per bucket, plus an "all" row for the overall series.
    _overall_stats = players.select(
        pl.lit("all").alias("games_bucket"),
        pl.col("rating").min().alias("min"),
        pl.col("rating").quantile(0.25).alias("q1"),
        pl.col("rating").median().alias("median"),
        pl.col("rating").mean().alias("mean"),
        pl.col("rating").quantile(0.75).alias("q3"),
        pl.col("rating").max().alias("max"),
        pl.len().alias("n"),
    )
    _group_stats = players_bucketed.group_by("games_bucket").agg(
        pl.col("rating").min().alias("min"),
        pl.col("rating").quantile(0.25).alias("q1"),
        pl.col("rating").median().alias("median"),
        pl.col("rating").mean().alias("mean"),
        pl.col("rating").quantile(0.75).alias("q3"),
        pl.col("rating").max().alias("max"),
        pl.len().alias("n"),
    )
    _stats = pl.concat([_overall_stats, _group_stats])
    _order = ["all", *bucket_order]

    # "all" is blue; groups use the non-blue palette.
    _group_palette = [
        "#f58518", "#54a24b", "#e45756", "#72b7b2",
        "#eeca3b", "#b279a2", "#ff9da6", "#9d755d", "#bab0ac",
    ]
    _range = ["#4c78a8"] + [
        _group_palette[i % len(_group_palette)] for i in range(len(bucket_order))
    ]

    _x_scale = alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False)
    _x_axis = alt.Axis(
        values=RATING_TICKS,
        format="d",
        labelAngle=0,
        grid=True,
        domainWidth=1,
        tickWidth=1,
    )
    _y = alt.Y(
        "games_bucket:N",
        sort=_order,
        title="games played (g)",
        axis=alt.Axis(grid=True, domainWidth=1, tickWidth=1),
    )
    _select = alt.selection_point(
        fields=["games_bucket"], bind="legend", toggle="true"
    )
    _color = alt.Color(
        "games_bucket:N",
        sort=_order,
        scale=alt.Scale(domain=_order, range=_range),
        title="games played (g)",
    )
    _opacity = alt.condition(_select, alt.value(1.0), alt.value(0.1))

    _tooltip = [
        alt.Tooltip("games_bucket:N", title="games"),
        alt.Tooltip("min:Q", format=",.1f", title="min"),
        alt.Tooltip("q1:Q", format=",.1f", title="q1"),
        alt.Tooltip("median:Q", format=",.1f", title="median"),
        alt.Tooltip("mean:Q", format=",.1f", title="mean"),
        alt.Tooltip("q3:Q", format=",.1f", title="q3"),
        alt.Tooltip("max:Q", format=",.1f", title="max"),
        alt.Tooltip("n:Q", format=",", title="n"),
    ]

    _base = alt.Chart(_stats).add_params(_select)

    _whisker = _base.mark_rule(size=1).encode(
        x=alt.X("min:Q", title="rating", scale=_x_scale, axis=_x_axis),
        x2="max:Q",
        y=_y,
        color=_color,
        opacity=_opacity,
        tooltip=_tooltip,
    )

    _box = _base.mark_bar(size=22).encode(
        x=alt.X("q1:Q", scale=_x_scale),
        x2="q3:Q",
        y=_y,
        color=_color,
        opacity=_opacity,
        tooltip=_tooltip,
    )

    _median_tick = _base.mark_tick(
        size=22,
        thickness=2,
        color="white",
    ).encode(
        x=alt.X("median:Q", scale=_x_scale),
        y=_y,
        opacity=_opacity,
        tooltip=_tooltip,
    )

    boxplot = alt.layer(_whisker, _box, _median_tick).properties(
        height=420,
        width="container",
        title="Pixie Chess: Rating Boxplots by Games Played",
    )
    boxplot
    return (boxplot,)


@app.cell
def __(mo):
    mo.md("## Rating CDF by Games Played")
    return


@app.cell
def __(
    RATING_MAX,
    RATING_MIN,
    RATING_TICKS,
    alt,
    bucket_order,
    pl,
    players,
    players_bucketed,
):
    # Combine per-bucket data with an "all" series so both render from
    # a single dataset and share one legend.
    _overall = players.select(pl.col("rating")).with_columns(
        pl.lit("all").alias("games_bucket")
    )
    _combined = pl.concat(
        [
            _overall,
            players_bucketed.select(["rating", "games_bucket"]),
        ]
    )
    _order = ["all", *bucket_order]

    # "all" is blue; groups use the non-blue palette.
    _group_palette = [
        "#f58518", "#54a24b", "#e45756", "#72b7b2",
        "#eeca3b", "#b279a2", "#ff9da6", "#9d755d", "#bab0ac",
    ]
    _range = ["#4c78a8"] + [
        _group_palette[i % len(_group_palette)] for i in range(len(bucket_order))
    ]

    _select = alt.selection_point(
        fields=["games_bucket"], bind="legend", toggle="true"
    )
    cdf = (
        alt.Chart(_combined)
        .add_params(_select)
        .transform_window(
            cumulative="count()",
            sort=[{"field": "rating"}],
            groupby=["games_bucket"],
        )
        .transform_joinaggregate(
            total="count()",
            groupby=["games_bucket"],
        )
        .transform_calculate(pct="datum.cumulative / datum.total")
        .mark_line(interpolate="step-after", strokeWidth=2)
        .encode(
            x=alt.X(
                "rating:Q",
                title="rating",
                scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
                axis=alt.Axis(
                    values=RATING_TICKS,
                    format="d",
                    labelAngle=0,
                    grid=True,
                    domainWidth=1,
                    tickWidth=1,
                ),
            ),
            y=alt.Y(
                "pct:Q",
                title="cumulative share",
                axis=alt.Axis(
                    format=".0%",
                    grid=True,
                    domainWidth=1,
                    tickWidth=1,
                ),
            ),
            color=alt.Color(
                "games_bucket:N",
                sort=_order,
                title="games played (g)",
                scale=alt.Scale(domain=_order, range=_range),
            ),
            opacity=alt.condition(_select, alt.value(1.0), alt.value(0.1)),
            tooltip=[
                alt.Tooltip("games_bucket:N", title="games"),
                alt.Tooltip("rating:Q", title="rating", format=",.1f"),
                alt.Tooltip("pct:Q", title="share", format=".1%"),
            ],
        )
        .properties(
            height=420,
            width="container",
            title="Pixie Chess: Rating CDF by Games Played",
        )
        .interactive(bind_y=False)
    )
    cdf
    return (cdf,)


if __name__ == "__main__":
    app.run()
