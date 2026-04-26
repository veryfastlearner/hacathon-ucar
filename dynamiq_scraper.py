#!/usr/bin/env python3
"""
Advanced Web Scraper for JavaScript-Heavy Websites
Works with: Times Higher Education, QS Rankings, Shanghai Rankings, etc.
Uses Playwright to render JavaScript before scraping
"""

from playwright.async_api import async_playwright
import pandas as pd
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class DynamicWebScraper:
    def __init__(self):
        self.data = []
        
    async def scrape_times_higher_education(self, url):
        """
        Scrape Times Higher Education rankings
        Waits for JavaScript to render before extracting data
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"Loading: {url}")
            await page.goto(url, wait_until="networkidle")
            
            # Wait for ranking data to load
            await page.wait_for_selector('[class*="ranking"]', timeout=10000)
            
            # Extract university ranking data
            rankings = await page.evaluate("""
                () => {
                    const data = [];
                    
                    // Look for ranking tables/cards
                    const rankingElements = document.querySelectorAll(
                        '[class*="ranking"], [class*="score"], [class*="metric"]'
                    );
                    
                    rankingElements.forEach(el => {
                        const text = el.innerText;
                        const html = el.innerHTML;
                        if (text.trim().length > 0) {
                            data.push({
                                text: text.trim(),
                                element: el.className
                            });
                        }
                    });
                    
                    return data;
                }
            """)
            
            logger.info(f"Found {len(rankings)} ranking elements")
            self.data.extend(rankings)
            
            # Get page title
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            await browser.close()
            return rankings

    async def scrape_qs_rankings(self, url):
        """
        Scrape QS World University Rankings
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"Loading QS Rankings: {url}")
            await page.goto(url, wait_until="networkidle")
            
            # Wait for content
            await page.wait_for_timeout(3000)
            
            # Extract all visible text
            content = await page.evaluate("() => document.body.innerText")
            
            logger.info("Extracted page content (first 500 chars):")
            logger.info(content[:500])
            
            self.data.append({
                'source': 'QS Rankings',
                'url': url,
                'content_preview': content[:1000],
                'timestamp': datetime.now().isoformat()
            })
            
            await browser.close()
            return content

    async def scrape_shanghai_rankings(self, url):
        """
        Scrape Shanghai Ranking of Academic Performance (SRAP)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"Loading Shanghai Rankings: {url}")
            await page.goto(url, wait_until="networkidle")
            
            # Extract table data
            table_data = await page.evaluate("""
                () => {
                    const data = [];
                    const tables = document.querySelectorAll('table');
                    
                    tables.forEach(table => {
                        const rows = table.querySelectorAll('tr');
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td, th');
                            const rowData = [];
                            cells.forEach(cell => {
                                rowData.push(cell.innerText.trim());
                            });
                            if (rowData.length > 0) {
                                data.push(rowData);
                            }
                        });
                    });
                    
                    return data;
                }
            """)
            
            logger.info(f"Found {len(table_data)} rows of ranking data")
            self.data.extend(table_data)
            
            await browser.close()
            return table_data

    async def generic_dynamic_scraper(self, url):
        """
        Generic scraper for any JavaScript-heavy website
        Extracts: headings, tables, lists, and structured data
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"Loading: {url}")
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(2000)  # Wait for JS to finish
            
            # Extract structured data
            extracted = await page.evaluate("""
                () => {
                    const result = {
                        title: document.title,
                        headings: [],
                        tables: [],
                        lists: [],
                        text_content: []
                    };
                    
                    // Get all headings
                    document.querySelectorAll('h1, h2, h3, h4').forEach(h => {
                        result.headings.push({
                            level: h.tagName,
                            text: h.innerText.trim()
                        });
                    });
                    
                    // Get all tables
                    document.querySelectorAll('table').forEach(table => {
                        const rows = [];
                        table.querySelectorAll('tr').forEach(tr => {
                            const cells = [];
                            tr.querySelectorAll('td, th').forEach(cell => {
                                cells.push(cell.innerText.trim());
                            });
                            rows.push(cells);
                        });
                        result.tables.push(rows);
                    });
                    
                    // Get text content (first 2000 chars)
                    result.text_content = document.body.innerText.substring(0, 2000);
                    
                    return result;
                }
            """)
            
            logger.info(f"Title: {extracted['title']}")
            logger.info(f"Headings: {len(extracted['headings'])}")
            logger.info(f"Tables: {len(extracted['tables'])}")
            
            self.data.append(extracted)
            
            await browser.close()
            return extracted

    def save_to_excel(self, filename='rankings_data.xlsx'):
        """Save extracted data to Excel"""
        if not self.data:
            logger.warning("No data to save")
            return
        
        df = pd.DataFrame(self.data)
        output_path = f'/mnt/user-data/outputs/{filename}'
        df.to_excel(output_path, index=False)
        logger.info(f"Data saved to: {output_path}")

    def save_to_csv(self, filename='rankings_data.csv'):
        """Save extracted data to CSV"""
        if not self.data:
            logger.warning("No data to save")
            return
        
        df = pd.DataFrame(self.data)
        output_path = f'/mnt/user-data/outputs/{filename}'
        df.to_csv(output_path, index=False)
        logger.info(f"Data saved to: {output_path}")


async def main():
    scraper = DynamicWebScraper()
    
    # Example 1: Times Higher Education Rankings
    print("\n" + "="*60)
    print("SCRAPING TIMES HIGHER EDUCATION RANKINGS")
    print("="*60)
    try:
        await scraper.scrape_times_higher_education(
            "https://www.timeshighereducation.com/world-university-rankings/university-carthage"
        )
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Generic dynamic website
    print("\n" + "="*60)
    print("GENERIC DYNAMIC WEBSITE SCRAPER")
    print("="*60)
    try:
        await scraper.generic_dynamic_scraper(
            "https://www.timeshighereducation.com/world-university-rankings/university-carthage"
        )
    except Exception as e:
        print(f"Error: {e}")
    
    # Save results
    if scraper.data:
        scraper.save_to_excel('rankings_extracted.xlsx')
        scraper.save_to_csv('rankings_extracted.csv')
        print("\n✓ Data saved!")
    else:
        print("\n⚠ No data extracted. Website structure may be different.")


if __name__ == "__main__":
    print("Installing Playwright (first run only)...")
    print("Run: playwright install")
    print("\nThen run this script: python dynamic_scraper.py")
    print("\nOr run directly:")
    asyncio.run(main())