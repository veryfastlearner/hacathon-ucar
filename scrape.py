#!/usr/bin/env python3
"""
UCAR Web Scraper - Fast institutional data extraction
Optimized for: Enrollment, Academic, Financial, HR, Research, Infrastructure, Partnership data
Output: CSV + Excel with automatic categorization
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UCARScraper:
    def __init__(self, base_url="https://ucar.rnu.tn/", max_retries=3):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.max_retries = max_retries
        self.visited_urls = set()
        self.data_by_category = defaultdict(list)
        self.errors = []

    def is_valid_url(self, url):
        """Check if URL belongs to UCAR and hasn't been visited"""
        try:
            parsed = urlparse(url)
            domain = self.base_url.replace('https://', '').replace('http://', '').rstrip('/')
            return (domain in parsed.netloc 
                    and url not in self.visited_urls)
        except:
            return False

    def fetch_page(self, url, timeout=10):
        """Fetch page with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/{self.max_retries} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.errors.append({"url": url, "error": str(e)})
                    return None

    def extract_data(self, soup, url):
        """Extract institutional data from page"""
        data_items = []
        
        # Extract tables
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])] if rows else []
            
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all('td')]
                if cells:
                    row_dict = dict(zip(headers, cells)) if headers else {'data': ' | '.join(cells)}
                    row_dict['source_url'] = url
                    row_dict['extracted_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                    data_items.append(row_dict)
        
        # Extract structured lists (enrollment, partnerships, etc.)
        for section in soup.find_all(['section', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['enrollment', 'academic', 'finance', 'hr', 'research', 'infrastructure', 'partnership']
        )):
            content = section.get_text(strip=True)
            if len(content) > 50:
                data_items.append({
                    'category': section.get('class', ['content'])[0],
                    'content': content[:500],
                    'source_url': url,
                    'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
        
        return data_items

    def categorize_data(self, data_items, url):
        """Categorize extracted data by type"""
        categories = ['enrollment', 'academic', 'finance', 'hr', 'research', 'infrastructure', 'partnership', 'general']
        
        for item in data_items:
            categorized = False
            for category in categories:
                if category in str(item).lower():
                    self.data_by_category[category].append(item)
                    categorized = True
                    break
            if not categorized:
                self.data_by_category['general'].append(item)

    def scrape(self, start_url=None, max_pages=500):
        """Main scraping loop"""
        if start_url is None:
            start_url = self.base_url
        
        urls_to_visit = [start_url]
        pages_scraped = 0

        while urls_to_visit and pages_scraped < max_pages:
            url = urls_to_visit.pop(0)
            
            if not self.is_valid_url(url) or url in self.visited_urls:
                continue

            self.visited_urls.add(url)
            logger.info(f"Scraping ({pages_scraped+1}/{max_pages}): {url}")
            
            html = self.fetch_page(url)
            if not html:
                continue

            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data
            data_items = self.extract_data(soup, url)
            self.categorize_data(data_items, url)
            
            # Find new URLs to visit
            for link in soup.find_all('a', href=True):
                new_url = urljoin(url, link['href'])
                if self.is_valid_url(new_url):
                    urls_to_visit.append(new_url)
            
            pages_scraped += 1
            time.sleep(1)  # Respectful rate limiting

        logger.info(f"Scraping complete. Pages: {pages_scraped}, Errors: {len(self.errors)}")
        return pages_scraped

    def export_to_excel(self, output_file='ucar_data.xlsx'):
        """Export categorized data to Excel with multiple sheets"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for category, items in self.data_by_category.items():
                if items:
                    df = pd.DataFrame(items)
                    df.to_excel(writer, sheet_name=category[:31], index=False)  # Sheet name limit: 31 chars
                    logger.info(f"Exported {len(items)} rows to '{category}' sheet")
            
            # Summary sheet
            summary_data = {
                'Category': list(self.data_by_category.keys()),
                'Records': [len(items) for items in self.data_by_category.values()],
                'Export Date': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Excel file saved: {output_file}")

    def export_to_csv(self, output_prefix='ucar_data'):
        """Export each category to separate CSV files"""
        for category, items in self.data_by_category.items():
            if items:
                df = pd.DataFrame(items)
                filename = f"{output_prefix}_{category}.csv"
                df.to_csv(filename, index=False)
                logger.info(f"CSV exported: {filename}")

if __name__ == "__main__":
    # Initialize scraper
    scraper = UCARScraper(base_url="https://ucar.rnu.tn/")
    
    # Run scraper (limit to 100 pages for testing)
    pages = scraper.scrape(max_pages=100)
    
    # Export results
    scraper.export_to_excel('ucar_data.xlsx')
    scraper.export_to_csv('ucar_data')
    
    # Print summary
    print("\n=== SCRAPING SUMMARY ===")
    print(f"Pages scraped: {pages}")
    print(f"Total errors: {len(scraper.errors)}")
    print("\nData by category:")
    for cat, items in scraper.data_by_category.items():
        print(f"  {cat}: {len(items)} records")