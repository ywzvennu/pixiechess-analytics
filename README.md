# pixiechess-analytics

Interactive web dashboard for [Pixie Chess](https://www.pixiechess.xyz/) analytics,
built with [marimo](https://marimo.io/), [Altair](https://altair-viz.github.io/),
and [Polars](https://pola.rs/).

## What's inside

- **Rating distribution** — histogram of all player ratings with mean/median/initial rules.
- **Games played distribution** — histogram of games played per player, with a log y-axis toggle.
- **Rating boxplots by games played** — one box per games-played bucket (`g = 1`, `g ∈ [2, 4]`, …), plus an `all` row, with min/q1/median/mean/q3/max in the tooltip.
- **Rating CDF by games played** — empirical CDFs overlaid per bucket, with an `all` series for the overall distribution.

Data lives in `data/players.jsonl` (one JSON object per line with `rating` and `games_played`).

## Develop

```bash
uv sync
uv run marimo edit dashboard.py
```

## Serve locally

```bash
uv run marimo run dashboard.py
```

Add `--host 0.0.0.0 --port 8080 --headless` for a server deployment.

## Deploy to GitHub Pages

The dashboard is exported to a static WASM bundle and published via GitHub Actions
(`.github/workflows/pages.yml`).

1. Push to `main`.
2. Repo → Settings → Pages → Source: **GitHub Actions**.
3. The site publishes at `https://<user>.github.io/pixiechess-analytics/`.

To build the static site locally:

```bash
uv run marimo export html-wasm dashboard.py -o site --mode run
uv run python -m http.server -d site 8000
```
