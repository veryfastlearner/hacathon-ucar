#!/usr/bin/env python3
"""
THE Rankings Scraper - Extract University of Carthage KPIs from Times Higher Education
Extracts: WUR Rankings, Subject Rankings, Impact Rankings, Key Student Stats, Subjects Taught
Output: CSV + Excel with structured sheets
"""

import requests
import re
import json
import pandas as pd
from collections import defaultdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class THERankingScraper:
    def __init__(self, profile_url="https://www.timeshighereducation.com/world-university-rankings/university-carthage", max_retries=3):
        self.profile_url = profile_url
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.data_by_category = defaultdict(list)
        self.errors = []
        self._raw_data = None

    def fetch_next_data(self):
        """Fetch the page and extract __NEXT_DATA__ JSON from SSR HTML"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching THE profile page: {self.profile_url}")
                response = self.session.get(self.profile_url, timeout=15)
                response.raise_for_status()

                match = re.search(
                    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                    response.text
                )
                if not match:
                    raise ValueError("No __NEXT_DATA__ script tag found in HTML")

                data = json.loads(match.group(1))
                self._raw_data = data.get('props', {}).get('pageProps', {})
                logger.info("Successfully extracted __NEXT_DATA__ from THE page")
                return True

            except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Attempt {attempt+1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    self.errors.append({"url": self.profile_url, "error": str(e)})
                    return False

    def extract_wur_rankings(self):
        """Extract World University Rankings with pillar scores per year"""
        gra_data = self._raw_data.get('viewProps', {}).get('wurRankingsGRAData', [])
        if not gra_data:
            logger.warning("No WUR rankings GRA data found")
            return

        for release in gra_data:
            year = release.get('year', '')
            name = release.get('name', '')
            for level1 in release.get('level1s', []):
                subject_name = level1.get('name', '')
                subject_key = level1.get('key', '')
                result = level1.get('result', {})
                score = result.get('score', {})
                rank = result.get('rank', {})

                self.data_by_category['wur_rankings'].append({
                    'year': year,
                    'release_name': name,
                    'subject': subject_name,
                    'subject_key': subject_key,
                    'score_lower': score.get('lower'),
                    'score_higher': score.get('higher'),
                    'rank_display': rank.get('displayRank'),
                    'rank_lower': rank.get('lower'),
                    'rank_higher': rank.get('higher'),
                    'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                })

                # Extract detailed pillar scores (level2s) — the dashboard data
                for level2 in level1.get('level2s') or []:
                    l2_result = level2.get('result', {})
                    l2_score = l2_result.get('score')
                    self.data_by_category['wur_pillar_scores'].append({
                        'year': year,
                        'release_name': name,
                        'subject': subject_name,
                        'subject_key': subject_key,
                        'pillar': level2.get('name', ''),
                        'score': l2_score,
                        'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    })

        logger.info(f"Extracted {len(self.data_by_category['wur_rankings'])} WUR ranking records")
        logger.info(f"Extracted {len(self.data_by_category['wur_pillar_scores'])} WUR pillar score records")

    def extract_subject_rankings(self):
        """Extract subject rankings from GRA data"""
        subjects_data = self._raw_data.get('viewProps', {}).get('subjectsGRAData', {})
        level1s = subjects_data.get('level1s', [])
        if not level1s:
            logger.warning("No subject rankings GRA data found")
            return

        for subject in level1s:
            result = subject.get('result', {})
            rank = result.get('rank', {})

            self.data_by_category['subject_rankings'].append({
                'subject': subject.get('name', ''),
                'subject_key': subject.get('key', ''),
                'rank_display': rank.get('displayRank'),
                'rank_lower': rank.get('lower'),
                'rank_higher': rank.get('higher'),
                'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            })

        logger.info(f"Extracted {len(self.data_by_category['subject_rankings'])} subject ranking records")

    def extract_student_stats(self):
        """Extract key student statistics per year"""
        stats_data = self._raw_data.get('viewProps', {}).get('keyStatsGRAData', [])
        if not stats_data:
            logger.warning("No key student stats GRA data found")
            return

        for release in stats_data:
            year = release.get('year', '')
            name = release.get('name', '')
            for item in release.get('institutionsData', {}).get('data', []):
                self.data_by_category['student_stats'].append({
                    'year': year,
                    'release_name': name,
                    'total_students': item.get('totalStudents'),
                    'female_student_pct': item.get('femaleStudentPercentage'),
                    'international_student_pct': item.get('internationalStudentPercentage'),
                    'students_per_staff': item.get('studentsPerStaff'),
                    'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                })

        logger.info(f"Extracted {len(self.data_by_category['student_stats'])} student stat records")

    def extract_impact_rankings(self):
        """Extract Impact Rankings (SDG scores and ranks)"""
        impact_data = self._raw_data.get('viewProps', {}).get('impactRankingsGRAData', [])
        if not impact_data:
            logger.warning("No Impact Rankings GRA data found")
            return

        for release in impact_data:
            year = release.get('year', '')
            name = release.get('name', '')
            for level1 in release.get('level1s', []):
                result = level1.get('result', {})
                score = result.get('score', {})
                rank = result.get('rank', {})

                self.data_by_category['impact_rankings'].append({
                    'year': year,
                    'release_name': name,
                    'sdg': level1.get('name', ''),
                    'sdg_key': level1.get('key', ''),
                    'score_lower': score.get('lower'),
                    'score_higher': score.get('higher'),
                    'rank_display': rank.get('displayRank'),
                    'rank_lower': rank.get('lower'),
                    'rank_higher': rank.get('higher'),
                    'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                })

        logger.info(f"Extracted {len(self.data_by_category['impact_rankings'])} impact ranking records")

    def extract_about(self):
        """Extract about/description text"""
        about = self._raw_data.get('viewProps', {}).get('about', {})
        description = about.get('description', {}).get('html', '')

        if description:
            self.data_by_category['about'].append({
                'title': about.get('title', ''),
                'subtitle': about.get('subtitle', ''),
                'description': description,
                'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            })
            logger.info("Extracted about/description data")

    def extract_subjects_taught(self):
        """Extract list of subjects taught"""
        subjects = self._raw_data.get('viewProps', {}).get('subjects', {})
        subjects_offered = subjects.get('subjectsOffered', [])

        for subject in subjects_offered:
            self.data_by_category['subjects_taught'].append({
                'subject_name': subject.get('name', ''),
                'label': subject.get('label', ''),
                'key': subject.get('key', ''),
                'wur31_code': subject.get('wur31code', ''),
                'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            })

        logger.info(f"Extracted {len(self.data_by_category['subjects_taught'])} subjects taught records")

    def extract_header_info(self):
        """Extract header/metadata info"""
        header = self._raw_data.get('headerProps', {})
        wur_rank = header.get('wurRankGRA', {})

        self.data_by_category['header_info'].append({
            'university_name': header.get('title', ''),
            'location': header.get('location', ''),
            'website': header.get('website', {}).get('href', ''),
            'wur_rank_year': wur_rank.get('year'),
            'wur_rank': wur_rank.get('rank'),
            'impact_currently_ranked': header.get('impactCurrentlyRanked'),
            'institution_id': self._raw_data.get('institutionId', ''),
            'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        })
        logger.info("Extracted header/metadata info")

    def scrape(self):
        """Run all extraction steps"""
        if not self.fetch_next_data():
            logger.error("Failed to fetch THE page data. Aborting.")
            return False

        self.extract_header_info()
        self.extract_about()
        self.extract_wur_rankings()
        self.extract_subject_rankings()
        self.extract_student_stats()
        self.extract_impact_rankings()
        self.extract_subjects_taught()

        total = sum(len(items) for items in self.data_by_category.values())
        logger.info(f"Scraping complete. Total records: {total}, Errors: {len(self.errors)}")
        return True

    def export_to_excel(self, output_file='the_ucar_rankings.xlsx'):
        """Export categorized data to Excel with multiple sheets"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for category, items in self.data_by_category.items():
                if items:
                    df = pd.DataFrame(items)
                    df.to_excel(writer, sheet_name=category[:31], index=False)
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

    def export_to_csv(self, output_prefix='the_ucar_rankings'):
        """Export each category to separate CSV files"""
        for category, items in self.data_by_category.items():
            if items:
                df = pd.DataFrame(items)
                filename = f"{output_prefix}_{category}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                logger.info(f"CSV exported: {filename}")


if __name__ == "__main__":
    scraper = THERankingScraper(
        profile_url="https://www.timeshighereducation.com/world-university-rankings/university-carthage"
    )

    success = scraper.scrape()

    if success:
        scraper.export_to_excel('the_ucar_rankings.xlsx')
        scraper.export_to_csv('the_ucar_rankings')

        print("\n=== THE RANKINGS SCRAPING SUMMARY ===")
        print(f"Total errors: {len(scraper.errors)}")
        print("\nData by category:")
        for cat, items in scraper.data_by_category.items():
            print(f"  {cat}: {len(items)} records")
    else:
        print("Scraping failed. Check errors above.")
