import asyncio
import aiohttp
import csv
import os
import re
import pandas as pd
from collections import deque
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from IPython.display import clear_output
import aiodns

class EmailScraper:
    def __init__(self, input_file, output_file, max_workers=50):
        self.input_file = input_file
        self.output_file = output_file
        self.stop_process = False
        self.max_workers = max_workers
        self.results = []  
        self.session = None
        self.dns_cache = {}
        self.dns_resolver = aiodns.DNSResolver()
        
        # Precompile patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
        
        # Invalid patterns
        self.invalid_domains = {
            'example.com', 'domain.com', 'yourdomain.com', 'mail.com', 
            'email.com', 'website.com', 'mydomain.com', 'site.com'
        }
        self.invalid_keywords = {
            'user', 'example', 'your', 'email', 'abc', 'xxx', 'xyz', 
            'exemple', 'zipify', 'username', 'someone', 'yourname', 
            'name', 'lorem', 'ipsum', 'test', 'demo', 'sample'
        }
        
        # Request settings
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.paths = ["", "/contact"]
        
    def _validate_url(self, url):
        return url if urlparse(url).scheme else f"http://{url}"

    async def validate_domain_async(self, email):
        try:
            domain = email.split('@')[-1]
            local_part = email.split('@')[0].lower()
            
            if domain in self.invalid_domains or any(keyword in local_part for keyword in self.invalid_keywords):
                return False
                
            if domain in self.dns_cache:
                return self.dns_cache[domain]
            
            try:
                await self.dns_resolver.query(domain, 'MX')
                self.dns_cache[domain] = True
                return True
            except Exception:
                self.dns_cache[domain] = False
                return False
                
        except Exception:
            return False

    def _extract_emails(self, text, soup):
        if not text:
            return []
        emails = set(self.email_pattern.findall(text))
        input_emails = {tag.get('value') for tag in soup.find_all('input', {'type': 'email'}) if tag.get('value')}
        bad_ext = {'.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.webp', '.svg'}
        return [email for email in (emails - input_emails) 
                if not any(email.lower().endswith(ext) for ext in bad_ext)]

    def _save_to_csv(self):
        if not self.results:
            return
            
        website_emails = {}
        for result in self.results:
            website = result['website']
            email = result['email']
            if website in website_emails:
                website_emails[website].append(email)
            else:
                website_emails[website] = [email]
        
        combined_rows = [
            {'website': website, 'email': ', '.join(set(emails))}
            for website, emails in website_emails.items()
        ]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['website', 'email'])
            writer.writeheader()
            writer.writerows(combined_rows)

    async def _fetch(self, session, url):
        try:
            for path in self.paths:
                full_url = urljoin(url, path)
                async with session.get(full_url, timeout=self.timeout) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception:
            pass
        return None

    async def _process_website(self, website):
        if self.stop_process:
            return []
        
        try:
            html = await self._fetch(self.session, self._validate_url(website))
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                emails = self._extract_emails(html, soup)
                
                if emails:
                    validation_tasks = [self.validate_domain_async(email) for email in emails]
                    validation_results = await asyncio.gather(*validation_tasks)
                    
                    valid_results = [
                        {'website': website, 'email': email}
                        for email, is_valid in zip(emails, validation_results)
                        if is_valid
                    ]
                    if valid_results:
                        self.results.extend(valid_results)
                    return valid_results
        except Exception as e:
            print(f"Error processing {website}: {str(e)}")
        
        return []

    async def scrape_emails(self):
        websites = pd.read_csv(self.input_file)['Address'].dropna().unique()
        total_websites = len(websites)
        processed = 0

        connector = aiohttp.TCPConnector(
            limit=self.max_workers,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
            force_close=True,
            ssl=False  
        )
        
        async with aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0"}, 
            connector=connector,
            timeout=self.timeout
        ) as session:
            self.session = session
            
            chunk_size = self.max_workers * 2
            for i in range(0, len(websites), chunk_size):
                chunk = websites[i:i + chunk_size]
                tasks = [self._process_website(website) for website in chunk]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                processed += len(chunk)
                clear_output(wait=True)
                print(f"Progress: {processed}/{total_websites} websites processed ({(processed/total_websites)*100:.2f}%)")
            
            self._save_to_csv()

        print(f"\nScraping completed. Results saved in {self.output_file}")
