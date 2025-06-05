# Thai Scraper

This project contains scripts for scraping Thai recipe websites and extracting contact information.

## Installation

Install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

## Environment Variables

- `SERPER_API_KEY` - API key for [Serper](https://serper.dev) used in `serper_scraper.py` to perform Google search API requests. Set this variable in your environment before running the script, for example:

```bash
export SERPER_API_KEY=your_key_here
```

## Usage

### `serper_scraper.py`

Queries the Serper API for Thai recipe sites, visits the results and saves found e‑mails to `result.csv`.
Run it with:

```bash
python3 serper_scraper.py
```

### `scrape_thai_recipes.py`

Fetches Google result pages directly without using the API. The collected data is also written to `result.csv`.
By default the script searches Google for the phrase `"thai dishes recipies"`.
Run it with:

```bash
python3 scrape_thai_recipes.py
```

After running either script, check the generated `result.csv` file for the output.
