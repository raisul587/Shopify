# Shopify Scraper (Websites + Emails)

This modular project organizes the original `website_scraper.py` (Shopify websites list scraper) and `email_scraper.py` (email crawler) into a reusable package without changing functionality of the classes.

## Structure

- `shopify_scraper/`
  - `__init__.py` exports `WebScraper` and `EmailScraper`
  - `website_scraper.py` contains the `WebScraper` class
  - `email_scraper.py` contains the `EmailScraper` class
- `cli.py` simple command line interface
- `requirements.txt`

Your original files remain untouched.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

Run with Python:

- Scrape Shopify websites list (pages -> CSV):

```bash
python cli.py scrape-sites --start 100 --end 130 --out scraped_data.csv
```

- Scrape emails from websites CSV:

```bash
python cli.py scrape-emails --in scraped_data.csv --out scraped_emails.csv --workers 50
```

- Full pipeline (sites then emails):

```bash
python cli.py pipeline --start 100 --end 130 --sites-out scraped_data.csv --emails-out scraped_emails.csv --workers 50
```

Notes:
- The CSV produced by the website scraper contains an `Address` column used by the email scraper.
- On Windows, the email scraper automatically uses `WindowsSelectorEventLoopPolicy`.
- The classes `WebScraper` and `EmailScraper` remain identical in logic to the originals.
