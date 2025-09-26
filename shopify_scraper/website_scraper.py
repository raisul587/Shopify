import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from IPython.display import clear_output
from datetime import datetime

class WebScraper:
    def __init__(self, start_page=1, end_page=10):
        self.start_page = start_page
        self.end_page = end_page
        self.driver = None
        self.data = {
            "Address": [],
            "IP": [],
            "Host": [],
            "Server Location": [],
            "Popularity Rank": []
        }

    def _initialize_driver(self):
        """Initialize ChromeDriver with minimal options."""
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-webgl')
        chrome_options.add_argument('--disable-webgl2')
        chrome_options.page_load_strategy = 'eager'
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add performance preferences
        prefs = {
            'profile.default_content_setting_values.images': 2,
            'profile.managed_default_content_settings.images': 2,
            'disk-cache-size': 4096
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(10)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def _handle_consent_popup(self):
        """Handle consent popup with multiple selector attempts."""
        try:
            # Try clicking the button directly
            button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-cta-do-not-consent"))
            )
            button.click()
            print("Clicked 'Do not consent' button")
            return True
        except:
            try:
                # Try clicking by XPath
                button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[2]/div[2]/div[2]/div[2]/button[2]"))
                )
                button.click()
                print("Clicked 'Do not consent' button using XPath")
                return True
            except:
                return False

    def _get_page_url(self, page_number):
        """Construct the URL for the given page number."""
        return f"https://myip.ms/browse/sites/{page_number}/ipID/23.227.38.0/ipIDii/23.227.38.255/sort/2/asc/1/"

    def _handle_verification(self):
        """Handle verification button."""
        try:
            button = WebDriverWait(self.driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value=\"I'm a Human Being »\"]"))
            )
            button.click()
            return True
        except:
            return False

    def _check_limit_exceeded(self):
        """Check if page limit is exceeded."""
        return "You have exceeded page visit limit" in self.driver.page_source

    def scrape_pages(self):
        """Scrape data from pages."""
        self._initialize_driver()
        try:
            for page in range(self.start_page, self.end_page + 1):
                clear_output(wait=True)
                print(f"Scraping page {page}...")
                
                try:
                    self.driver.get(self._get_page_url(page))
                    time.sleep(2 if page == self.start_page else 0.05)

                    # Handle popups only on first page
                    if page == self.start_page:
                        for _ in range(2):
                            if self._handle_consent_popup():
                                break
                            time.sleep(0.2)
                        self._handle_verification()

                    if self._check_limit_exceeded():
                        print("\nPage limit exceeded! Saving data...")
                        break

                    # Parse page
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    addresses = soup.select("#sites_tbl > tbody > tr > td.row_name > a")

                    if not addresses:
                        continue

                    # Extract data
                    self.data["Address"].extend([item.get_text() for item in addresses])
                    self.data["IP"].extend([item.get_text() for item in soup.select("#sites_tbl > tbody > tr > td:nth-child(3) > a")])
                    self.data["Host"].extend([item.get_text() for item in soup.select("#sites_tbl > tbody > tr > td:nth-child(4) > a")])
                    self.data["Server Location"].extend([item.get_text() for item in soup.select("#sites_tbl > tbody > tr > td:nth-child(5) > a")])
                    self.data["Popularity Rank"].extend([item.get_text() for item in soup.select("#sites_tbl > tbody > tr > td:nth-child(7) > span")])

                except Exception as e:
                    print(f"Error on page {page}: {str(e)}")
                    continue

        finally:
            self.driver.quit()

    def save_to_csv(self, file_name):
        """Save scraped data to a CSV file."""
        if not self.data["Address"]:
            print("No data was collected!")
            return
            
        df = pd.DataFrame(self.data)
        df.to_csv(file_name, index=False)
        print(f"\nData saved to {file_name}")
        print(f"Total records collected: {len(df)}")
