#!/usr/bin/env python3
"""
UCAR Scrapy Spider - Industrial-strength scraper for 1000+ pages
Auto-detects academic, financial, HR, research, infrastructure data
Outputs directly to CSV/Excel
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import pandas as pd
from pathlib import Path

class UCARSpider(CrawlSpider):
    """Scrapy spider for University of Carthage data extraction"""
    
    name = 'ucar_spider'
    allowed_domains = ['ucar.rnu.tn']
    start_urls = ['https://ucar.rnu.tn/']
    
    # Rules for following links
    rules = (
        Rule(LinkExtractor(allow_domains=['ucar.rnu.tn']), 
             callback='parse_page', follow=True),
    )
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.5,
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'COOKIES_ENABLED': False,
        'RETRY_TIMES': 2,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []
        self.page_count = 0

    def parse_page(self, response):
        """Parse individual page and extract data"""
        self.page_count += 1
        
        # Extract tables
        for table in response.css('table'):
            headers = table.css('th::text, tr td:first-child::text').getall()
            for row in table.css('tbody tr'):
                cells = row.css('td::text').getall()
                if cells:
                    self.items.append({
                        'type': 'table',
                        'data': ' | '.join(cells),
                        'source': response.url
                    })
        
        # Extract section content with category detection
        for div in response.css('section, div[class*="content"]'):
            text = div.css('::text').getall()
            full_text = ' '.join(text).strip()
            
            if len(full_text) > 100:
                category = self.detect_category(full_text)
                self.items.append({
                    'category': category,
                    'content': full_text[:500],
                    'source': response.url
                })
        
        # Continue following links
        for link in response.css('a::attr(href)').getall():
            yield response.follow(link, callback=self.parse_page)

    def detect_category(self, text):
        """Auto-detect data category from content"""
        text_lower = text.lower()
        keywords = {
            'enrollment': ['étudiant', 'admission', 'inscri', 'enrollment', 'student', 'candidat'],
            'academic': ['cours', 'programme', 'diplôme', 'academic', 'pedagogie', 'module'],
            'finance': ['budget', 'financi', 'coût', 'dépens', 'revenue', 'salary', 'salaire'],
            'hr': ['personnel', 'ressources humaines', 'employee', 'staff', 'rh', 'hr'],
            'research': ['recherche', 'publication', 'projet', 'research', 'paper', 'grant'],
            'infrastructure': ['bâtiment', 'équipement', 'infrastructure', 'classroom', 'facility'],
            'partnership': ['partenariat', 'accord', 'collaboration', 'partner', 'agreement'],
        }
        
        for category, keywords_list in keywords.items():
            if any(kw in text_lower for kw in keywords_list):
                return category
        return 'general'

    def closed(self, reason):
        """Called when spider closes - export data"""
        df = pd.DataFrame(self.items)
        output_file = 'ucar_data.csv'
        df.to_csv(output_file, index=False)
        self.logger.info(f"Scraped {self.page_count} pages, {len(self.items)} items exported to {output_file}")

def run_scrapy_spider(max_pages=500):
    """Run the Scrapy spider"""
    process = CrawlerProcess({
        'CLOSESPIDER_PAGECOUNT': max_pages,
    })
    process.crawl(UCARSpider)
    process.start()

if __name__ == '__main__':
    run_scrapy_spider(max_pages=500)