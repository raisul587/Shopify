import argparse
import os
import asyncio

from shopify_scraper import WebScraper, EmailScraper


def run_scrape_sites(start_page: int, end_page: int, output_file: str):
    scraper = WebScraper(start_page=start_page, end_page=end_page)
    scraper.scrape_pages()
    scraper.save_to_csv(output_file)


def run_scrape_emails(input_file: str, output_file: str, max_workers: int):
    async def main():
        scraper = EmailScraper(input_file=input_file, output_file=output_file, max_workers=max_workers)
        await scraper.scrape_emails()

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


def run_pipeline(start_page: int, end_page: int, sites_output: str, emails_output: str, max_workers: int):
    run_scrape_sites(start_page, end_page, sites_output)
    run_scrape_emails(sites_output, emails_output, max_workers)


def parse_args():
    parser = argparse.ArgumentParser(description="Shopify website and email scraper")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # scrape-sites
    p_sites = subparsers.add_parser("scrape-sites", help="Scrape Shopify websites list")
    p_sites.add_argument("--start", type=int, default=1, help="Start page number")
    p_sites.add_argument("--end", type=int, default=10, help="End page number")
    p_sites.add_argument("--out", type=str, default="scraped_data.csv", help="Output CSV path for websites")

    # scrape-emails
    p_emails = subparsers.add_parser("scrape-emails", help="Scrape emails from websites CSV")
    p_emails.add_argument("--in", dest="input", type=str, default="scraped_data.csv", help="Input CSV path with websites (expects 'Address' column)")
    p_emails.add_argument("--out", type=str, default="scraped_emails.csv", help="Output CSV path for emails")
    p_emails.add_argument("--workers", type=int, default=50, help="Max concurrent workers")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Run full pipeline: websites then emails")
    p_pipe.add_argument("--start", type=int, default=1, help="Start page number")
    p_pipe.add_argument("--end", type=int, default=10, help="End page number")
    p_pipe.add_argument("--sites-out", type=str, default="scraped_data.csv", help="Intermediate sites CSV path")
    p_pipe.add_argument("--emails-out", type=str, default="scraped_emails.csv", help="Final emails CSV path")
    p_pipe.add_argument("--workers", type=int, default=50, help="Max concurrent workers")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == "scrape-sites":
        run_scrape_sites(args.start, args.end, args.out)
    elif args.command == "scrape-emails":
        run_scrape_emails(args.input, args.out, args.workers)
    elif args.command == "pipeline":
        run_pipeline(args.start, args.end, args.sites_out, args.emails_out, args.workers)


if __name__ == "__main__":
    main()
