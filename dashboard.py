import marimo

app = marimo.App(width="medium")


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
    players = pl.read_ndjson("data/players.jsonl")
    INITIAL_RATING = 1500
    return INITIAL_RATING, players


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
    mo.md("## Rating distribution")
    return


@app.cell
def __(INITIAL_RATING, alt, players):
    _mean = players["rating"].mean()
    _median = players["rating"].median()

    _hist = (
        alt.Chart(players)
        .mark_bar(opacity=0.75)
        .encode(
            x=alt.X("rating:Q", bin=alt.Bin(step=10), title="Rating"),
            y=alt.Y("count():Q", title="Players"),
            tooltip=[alt.Tooltip("count():Q", title="Players")],
        )
    )

    _rules = (
        alt.Chart(
            alt.InlineData(
                values=[
                    {"value": _mean, "label": f"mean: {_mean:.1f}"},
                    {"value": _median, "label": f"median: {_median:.1f}"},
                    {"value": INITIAL_RATING, "label": f"initial: {INITIAL_RATING}"},
                ]
            )
        )
        .mark_rule(strokeDash=[4, 4], size=2)
        .encode(
            x="value:Q",
            color=alt.Color("label:N", title=None),
            tooltip="label:N",
        )
    )

    rating_chart = (_hist + _rules).properties(
        height=360, title="Pixie Chess player ratings"
    )
    rating_chart
    return (rating_chart,)


@app.cell
def __(mo):
    mo.md("## Rating by games played")
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
def __(alt, bucket_order, players_bucketed):
    faceted = (
        alt.Chart(players_bucketed)
        .mark_bar(opacity=0.75)
        .encode(
            x=alt.X("rating:Q", bin=alt.Bin(step=10), title="Rating"),
            y=alt.Y("count():Q", title="Players"),
            color=alt.Color(
                "games_bucket:N",
                sort=bucket_order,
                legend=None,
            ),
        )
        .properties(height=140, width=640)
        .facet(
            row=alt.Row(
                "games_bucket:N",
                sort=bucket_order,
                title="Games played",
                header=alt.Header(labelAngle=0, labelAlign="left"),
            )
        )
        .resolve_scale(y="independent")
    )
    faceted
    return (faceted,)


@app.cell
def __(mo):
    mo.md("## Rating vs games played")
    return


@app.cell
def __(alt, players):
    scatter_base = alt.Chart(players)

    scatter = scatter_base.mark_circle(size=18, opacity=0.5).encode(
        x=alt.X("rating:Q", title="Rating", scale=alt.Scale(zero=False)),
        y=alt.Y(
            "games_played:Q",
            title="Games played (log)",
            scale=alt.Scale(type="log", base=10),
        ),
        tooltip=["rating:Q", "games_played:Q"],
    ).properties(height=360, width=640)

    top_hist = scatter_base.mark_bar(opacity=0.75).encode(
        x=alt.X("rating:Q", bin=alt.Bin(step=10), axis=None),
        y=alt.Y("count():Q", title=None),
    ).properties(height=80, width=640)

    right_hist = scatter_base.mark_bar(opacity=0.75).encode(
        y=alt.Y("games_played:Q", bin=alt.Bin(maxbins=40), axis=None),
        x=alt.X("count():Q", title=None),
    ).properties(height=360, width=80)

    joint = (top_hist & (scatter | right_hist)).properties(
        title="Rating vs games played"
    )
    joint
    return (joint,)


if __name__ == "__main__":
    app.run()
