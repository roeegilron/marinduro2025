# Marinduro Results Comparison

This project compares Marinduro stage times rider-by-rider. The default app is now a static GitHub Pages page that loads the 2026 Pro and Expert results directly from Race Result, so visitors do not need to clone the repository or upload a PDF.

## Features

- **Current-year results:** Loads the 2026 Marinduro Pro and Expert list from [Race Result](https://my.raceresult.com/395892/results#0_933E75).
- **GitHub Pages ready:** `index.html` is a no-build JavaScript app that can be served directly from GitHub Pages.
- **Rider comparison:** Select one primary rider and up to 10 comparison riders.
- **Comparison metrics:** Toggle between time differences and percentage differences.
- **Category and text filters:** Narrow the rider list by category, name, bib, city, or club.
- **Streamlit fallback:** `app.py` can still load the 2026 web results or parse an uploaded PDF locally.

## How It Works

1. `index.html` fetches the 2026 Race Result config for event `395892`.
2. It selects the `Online|Pro Race` list, whose Race Result list ID is `933E75`.
3. It downloads the list JSON, normalizes rider rows, and computes stage and overall deltas in the browser.
4. If the live request fails, the page falls back to the browser's cached copy or the bundled 2026 snapshot.

## Deploy On GitHub Pages

No build step is required.

1. Push the repository to GitHub.
2. In the repository settings, open **Pages**.
3. Set the source to the branch that contains `index.html`.
4. Use the repository root as the Pages folder.

GitHub Pages will serve `index.html` as the site homepage.

## Run The Optional Streamlit App

The Python app is useful for local debugging or comparing an uploaded PDF.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501` after Streamlit starts.

## Data Source

The current hard-coded source is the 2026 Marinduro Race Result page:

```text
https://my.raceresult.com/395892/results#0_933E75
```

The static page uses the public Race Result JSON endpoints behind that widget. If a future event uses a new event ID or list ID, update the constants near the top of `index.html` and `app.py`.

`results-2026-pro-race.snapshot.json` is a bundled copy of the same 2026 Pro and Expert results. It lets the GitHub Pages site work off the bat even if Race Result is temporarily unavailable.

## Troubleshooting

- **Static page does not load live results:** Refresh the page and check that the Race Result page is still public.
- **No riders appear after filtering:** Clear the text filter or switch the category back to `All categories`.
- **PDF parsing issues in Streamlit:** Ensure the uploaded PDF follows the same result-table layout as the Race Result export.
