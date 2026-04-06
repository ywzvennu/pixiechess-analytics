import marimo

app = marimo.App(width="full", app_title="Pixie Chess Analytics")


@app.cell
def __():
    import marimo as mo
    import altair as alt
    import polars as pl
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
def __(pl):
    import math

    players = pl.read_ndjson("data/players.jsonl")
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
        - **Mean rating:** {players['rating'].mean():.1f}
        - **Median rating:** {players['rating'].median():.1f}
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
                title="Rating",
                scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
                axis=alt.Axis(values=RATING_TICKS, format="d", labelAngle=0),
            ),
            y=alt.Y(
                "count():Q",
                title="Players",
                axis=alt.Axis(format="d", tickMinStep=1),
            ),
            tooltip=[alt.Tooltip("count():Q", title="Players")],
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
                alt.Tooltip("value:Q", format=".1f", title="value"),
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
    games_log_y = mo.ui.switch(value=False, label="Log y-axis")
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
                title="Games Played",
                scale=alt.Scale(domain=[0, _domain_max], nice=False),
                axis=alt.Axis(format="d", labelAngle=0, tickMinStep=1),
            ),
            y=alt.Y(
                "count():Q",
                title="Players" + (" (log)" if games_log_y.value else ""),
                scale=alt.Scale(
                    type="log" if games_log_y.value else "linear",
                    base=10,
                ),
                axis=alt.Axis(format="d", tickMinStep=1),
            ),
            tooltip=[alt.Tooltip("count():Q", title="Players")],
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
                alt.Tooltip("value:Q", format=".1f", title="value"),
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
def __(mo):
    mo.md("## Rating Distribution by Games Played")
    return


@app.cell
def __(pl, players):
    # Bucket games played: [1], [2-4], [5-16], [17-64], ...
    _max_games = players["games_played"].max()
    _buckets = []
    _lo, _hi = 1, 1
    while _lo <= _max_games:
        label = f"g = {_lo}" if _lo == _hi else f"{_lo}–{_hi}"
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
def __(
    INITIAL_RATING,
    RATING_MAX,
    RATING_MIN,
    RATING_TICKS,
    alt,
    bucket_order,
    players_bucketed,
):
    _x = alt.X(
        "rating:Q",
        bin=alt.Bin(step=10, extent=[RATING_MIN, RATING_MAX]),
        title="Rating",
        scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
        axis=alt.Axis(values=RATING_TICKS, format="d", labelAngle=0),
    )

    # Bar palette for per-bucket groups — avoids colors used by the rule
    # lines (gray=initial, red=mean, purple=median) and the default blue
    # used by the overall rating chart.
    _palette = [
        "#f58518", "#72b7b2", "#eeca3b", "#b279a2",
        "#ff9da6", "#9d755d", "#bab0ac",
    ]
    _bar_range = [_palette[i % len(_palette)] for i in range(len(bucket_order))]

    _bars = alt.Chart().mark_bar(opacity=0.8).encode(
        x=_x,
        y=alt.Y(
            "count():Q",
            title="Players",
            axis=alt.Axis(format="d", tickMinStep=1),
        ),
        color=alt.Color(
            "games_bucket:N",
            sort=bucket_order,
            scale=alt.Scale(domain=bucket_order, range=_bar_range),
            legend=None,
        ),
    )

    _rules = (
        alt.Chart()
        .transform_aggregate(
            mean="mean(rating)",
            median="median(rating)",
            groupby=["games_bucket"],
        )
        .transform_calculate(initial=f"{INITIAL_RATING}")
        .transform_fold(["initial", "mean", "median"], as_=["label", "value"])
        .mark_rule(strokeDash=[4, 4], size=2)
        .encode(
            x=alt.X("value:Q"),
            color=alt.Color(
                "label:N",
                title=None,
                scale=alt.Scale(
                    domain=["initial", "mean", "median"],
                    range=["#7f7f7f", "#d62728", "#9467bd"],
                ),
            ),
            tooltip=["label:N", alt.Tooltip("value:Q", format=".1f")],
        )
    )

    faceted = (
        alt.layer(_bars, _rules, data=players_bucketed)
        .properties(height=220, width=820)
        .facet(
            row=alt.Row(
                "games_bucket:N",
                sort=bucket_order,
                title="Games Played",
                header=alt.Header(
                    labelFontSize=12,
                    labelAngle=0,
                    labelAlign="center",
                    labelAnchor="middle",
                    labelOrient="top",
                    titleOrient="left",
                ),
            )
        )
        .resolve_scale(y="independent")
        .properties(title="Pixie Chess: Rating Distribution by Games Played")
    )
    faceted
    return (faceted,)


@app.cell
def __(mo):
    mo.md("### Alternative: 2D Density Heatmap")
    return


@app.cell
def __(GAMES_MAX, GAMES_TICKS, RATING_MAX, RATING_MIN, RATING_TICKS, alt, players):
    heatmap = (
        alt.Chart(players)
        .mark_rect()
        .encode(
            x=alt.X(
                "rating:Q",
                bin=alt.Bin(step=25, extent=[RATING_MIN, RATING_MAX]),
                title="Rating",
                scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
                axis=alt.Axis(values=RATING_TICKS, format="d", labelAngle=0),
            ),
            y=alt.Y(
                "games_played:Q",
                bin=alt.Bin(maxbins=30),
                title="Games Played (log)",
                scale=alt.Scale(type="log", base=10, domain=[1, GAMES_MAX]),
                axis=alt.Axis(values=GAMES_TICKS, format="d"),
            ),
            color=alt.Color(
                "count():Q",
                title="Players",
                scale=alt.Scale(scheme="viridis"),
            ),
            tooltip=[alt.Tooltip("count():Q", title="Players")],
        )
        .properties(
            height=460,
            width="container",
            title="Pixie Chess: Rating × Games Played Density",
        )
    )
    heatmap
    return (heatmap,)


@app.cell
def __(mo):
    mo.md("### Alternative: Ridgeline Plot")
    return


@app.cell
def __(RATING_MAX, RATING_MIN, RATING_TICKS, alt, bucket_order, players_bucketed):
    _step = 60
    ridgeline = (
        alt.Chart(players_bucketed, height=_step)
        .transform_density(
            "rating",
            as_=["rating", "density"],
            groupby=["games_bucket"],
            extent=[RATING_MIN, RATING_MAX],
            steps=200,
        )
        .mark_area(
            interpolate="monotone",
            fillOpacity=0.7,
            stroke="#333",
            strokeWidth=0.8,
        )
        .encode(
            x=alt.X(
                "rating:Q",
                title="Rating",
                scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
                axis=alt.Axis(values=RATING_TICKS, format="d", labelAngle=0),
            ),
            y=alt.Y("density:Q", axis=None, scale=alt.Scale(range=[_step, -_step * 1.5])),
            color=alt.Color(
                "games_bucket:N",
                sort=bucket_order,
                legend=None,
            ),
            row=alt.Row(
                "games_bucket:N",
                sort=bucket_order,
                title="Games Played",
                header=alt.Header(
                    labelAngle=0,
                    labelAlign="left",
                    labelOrient="left",
                    labelFontSize=11,
                ),
            ),
        )
        .properties(width=820, bounds="flush", title="Pixie Chess: Rating Density by Games Played")
        .configure_facet(spacing=0)
        .configure_view(stroke=None)
    )
    ridgeline
    return (ridgeline,)


@app.cell
def __(mo):
    mo.md("### Alternative: Box Plot")
    return


@app.cell
def __(RATING_MAX, RATING_MIN, RATING_TICKS, alt, bucket_order, players_bucketed):
    boxplot = (
        alt.Chart(players_bucketed)
        .mark_boxplot(size=20, extent="min-max")
        .encode(
            x=alt.X(
                "rating:Q",
                title="Rating",
                scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
                axis=alt.Axis(values=RATING_TICKS, format="d", labelAngle=0),
            ),
            y=alt.Y(
                "games_bucket:N",
                sort=bucket_order,
                title="Games Played",
            ),
            color=alt.Color(
                "games_bucket:N",
                sort=bucket_order,
                legend=None,
            ),
        )
        .properties(
            height=max(180, 40 * len(bucket_order)),
            width="container",
            title="Pixie Chess: Rating Boxplots by Games Played",
        )
    )
    boxplot
    return (boxplot,)


@app.cell
def __(mo):
    mo.md("### Alternative: Empirical CDF Overlay")
    return


@app.cell
def __(RATING_MAX, RATING_MIN, RATING_TICKS, alt, bucket_order, players_bucketed):
    cdf = (
        alt.Chart(players_bucketed)
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
                title="Rating",
                scale=alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False),
                axis=alt.Axis(values=RATING_TICKS, format="d", labelAngle=0),
            ),
            y=alt.Y(
                "pct:Q",
                title="Cumulative Share",
                axis=alt.Axis(format=".0%"),
            ),
            color=alt.Color(
                "games_bucket:N",
                sort=bucket_order,
                title="Games Played",
            ),
            tooltip=[
                alt.Tooltip("games_bucket:N", title="Games"),
                alt.Tooltip("rating:Q", title="Rating"),
                alt.Tooltip("pct:Q", title="Share", format=".1%"),
            ],
        )
        .properties(
            height=460,
            width="container",
            title="Pixie Chess: Rating CDF by Games Played",
        )
        .interactive(bind_y=False)
    )
    cdf
    return (cdf,)


@app.cell
def __(mo):
    mo.md("## Rating vs Games Played")
    return


@app.cell
def __(
    GAMES_MAX,
    GAMES_TICKS,
    RATING_MAX,
    RATING_MIN,
    RATING_TICKS,
    alt,
    players,
):
    scatter_base = alt.Chart(players)
    _zoom = alt.selection_interval(bind="scales")

    _main_w, _main_h, _marg = 820, 480, 110
    _rating_scale = alt.Scale(domain=[RATING_MIN, RATING_MAX], nice=False)
    _games_scale = alt.Scale(type="log", base=10, domain=[1, GAMES_MAX])

    scatter = scatter_base.mark_circle(size=18, opacity=0.5).encode(
        x=alt.X(
            "rating:Q",
            title="Rating",
            scale=_rating_scale,
            axis=alt.Axis(values=RATING_TICKS, format="d", labelAngle=0),
        ),
        y=alt.Y(
            "games_played:Q",
            title="Games played (log)",
            scale=_games_scale,
            axis=alt.Axis(values=GAMES_TICKS, format="d"),
        ),
        tooltip=["rating:Q", "games_played:Q"],
    ).properties(height=_main_h, width=_main_w).add_params(_zoom)

    top_hist = scatter_base.mark_bar(opacity=0.75).encode(
        x=alt.X(
            "rating:Q",
            bin=alt.Bin(step=10, extent=[RATING_MIN, RATING_MAX]),
            scale=_rating_scale,
            axis=None,
        ),
        y=alt.Y(
            "count():Q",
            title=None,
            axis=alt.Axis(format="d", tickMinStep=1),
        ),
    ).properties(height=_marg, width=_main_w)

    right_hist = scatter_base.mark_bar(opacity=0.75).encode(
        y=alt.Y(
            "games_played:Q",
            bin=alt.Bin(maxbins=40),
            scale=_games_scale,
            axis=None,
        ),
        x=alt.X(
            "count():Q",
            title=None,
            axis=alt.Axis(format="d", tickMinStep=1),
        ),
    ).properties(height=_main_h, width=_marg)

    joint = alt.vconcat(
        top_hist,
        alt.hconcat(scatter, right_hist, spacing=4),
        spacing=4,
    ).properties(title="Pixie Chess: Rating vs Games Played")
    joint
    return (joint,)


if __name__ == "__main__":
    app.run()
