import marimo

app = marimo.App()


@app.cell
def __():
    import marimo as mo
    return (mo,)


@app.cell
def __(mo):
    mo.md(
        """
        # Pixie Chess Analytics

        Interactive dashboard for [Pixie Chess](https://www.pixiechess.xyz/) analytics.
        """
    )
    return


if __name__ == "__main__":
    app.run()
