# Thai Scraper

This repository contains two simple scripts for scraping Thai recipe websites.

## Requirements

- **Python**: 3.8 or later
- **Dependencies**: install via `pip install -r requirements.txt`

## Usage

### `scrape_thai_recipes.py`

Fetches Google search pages in basic HTML mode, extracts recipe domains, and searches for email addresses and contact links on those sites. The results are written to `result.csv`.

Run:

```bash
python3 scrape_thai_recipes.py
```

### `serper_scraper.py`

Uses the Serper.dev API to retrieve Google search results, then scans the discovered pages for email addresses. The output is also saved to `result.csv`.

Set your Serper API key in the environment before running:

```bash
export SERPER_API_KEY="<your key>"
python3 serper_scraper.py
```

## Output

Both scripts create a file named `result.csv` containing the scraped data. Columns differ slightly per script but generally include the timestamp, domain, page URL and any emails or contact links that were found.
