import logging
import pathlib
import re
import time
from datetime import datetime
from urllib.parse import urljoin

import html2text
import pandas as pd
import pydantic
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Article(pydantic.BaseModel):
    title: str
    url: str
    author: str
    first_published: str
    substantive_revision: str
    content_html: str
    content_markdown: str
    word_count: int
    scraped_at: str


class SepScraper:
    def __init__(self, base_url: str = 'https://plato.stanford.edu', delay: float = 1.0):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

        # Initialize HTML to Markdown converter
        self.h2m = html2text.HTML2Text()
        self.h2m.ignore_links = False
        self.h2m.ignore_images = False
        # Don't wrap lines
        self.h2m.body_width = 0
        self.h2m.unicode_snob = True

    def get_article_links(self) -> list[str]:
        logger.info('Fetching article links...')
        article_links = set()

        try:
            response = self.session.get(f'{self.base_url}/contents.html')
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('entries/'):
                    full_url = urljoin(self.base_url, href)
                    article_links.add(full_url)

        except Exception as e:
            logger.error(f'Error fetching main contents page: {e}')

        logger.info(f'Found {len(article_links)} article links')
        return list(article_links)

    def extract_metadata(self, soup: BeautifulSoup) -> dict[str, str]:
        metadata = {'title': '', 'author': '', 'first_published': '', 'substantive_revision': ''}

        # Extract title
        title_elem = soup.find('h1')
        if title_elem:
            metadata['title'] = title_elem.get_text().strip()

        # Extract publication info (usually in a specific div or paragraph)
        pub_info = soup.find('div', class_='pubinfo') or soup.find('p', class_='pubinfo')
        if pub_info:
            text = pub_info.get_text()

            # Extract author
            author_match = re.search(r'First published.*?by\s+([^,]+)', text, re.IGNORECASE)
            if not author_match:
                author_match = re.search(r'by\s+([^,\n]+)', text, re.IGNORECASE)
            if author_match:
                metadata['author'] = author_match.group(1).strip()

            # Extract first published date
            first_pub_match = re.search(r'First published\s+([^;,\n]+)', text, re.IGNORECASE)
            if first_pub_match:
                metadata['first_published'] = first_pub_match.group(1).strip()

            # Extract substantive revision date
            revision_match = re.search(r'substantive revision\s+([^;,\n]+)', text, re.IGNORECASE)
            if revision_match:
                metadata['substantive_revision'] = revision_match.group(1).strip()

        # Alternative method: look for author info in different locations
        if not metadata['author']:
            # Sometimes author is in a separate element
            author_elem = soup.find('div', class_='author') or soup.find('p', class_='author')
            if author_elem:
                metadata['author'] = author_elem.get_text().strip()

        return metadata

    def clean_content(self, soup: BeautifulSoup) -> str:
        # Remove navigation, headers, footers, etc.
        for elem in soup.find_all(['nav', 'header', 'footer']):
            elem.decompose()

        # Remove publication info (we extract it separately)
        for elem in soup.find_all(['div', 'p'], class_='pubinfo'):
            elem.decompose()

        # Remove other metadata sections
        for elem in soup.find_all(['div'], class_=['navigation', 'toc']):
            elem.decompose()

        # Find main content - usually in a div with id 'main-text' or similar
        main_content = soup.find('div', id='main-text') or soup.find('div', id='content') or soup.find('div', class_='entry') or soup.find('main')

        if main_content:
            # Remove any remaining unwanted elements
            for elem in main_content.find_all(['script', 'style']):
                elem.decompose()
            return str(main_content)
        else:
            # Fallback: get body content and clean it
            body = soup.find('body')
            if body:
                for elem in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                return str(body)

        return str(soup)

    def scrape_article(self, url: str) -> Article | None:
        try:
            logger.info(f'Scraping: {url}')
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract metadata
            metadata = self.extract_metadata(soup)

            # Extract and clean content
            content_html = self.clean_content(soup)

            # Convert to markdown
            content_markdown = self.h2m.handle(content_html)

            # Calculate word count (approximate)
            word_count = len(content_markdown.split())

            article = Article(
                title=metadata['title'],
                url=url,
                author=metadata['author'],
                first_published=metadata['first_published'],
                substantive_revision=metadata['substantive_revision'],
                content_html=content_html,
                content_markdown=content_markdown,
                word_count=word_count,
                scraped_at=datetime.now().isoformat(),
            )

            logger.info(f'Successfully scraped: {metadata["title"]}')
            return article

        except Exception as e:
            logger.error(f'Error scraping {url}: {e}')
            return None

    def scrape_all_articles(self, max_articles: int | None = None) -> list[Article]:
        article_links = self.get_article_links()

        if max_articles:
            article_links = article_links[:max_articles]
            logger.info(f'Limited to first {max_articles} articles')

        articles = []

        for i, url in enumerate(article_links, 1):
            logger.info(f'Progress: {i}/{len(article_links)}')

            article = self.scrape_article(url)
            if article:
                articles.append(article)

            # Add delay between requests
            time.sleep(self.delay)

        return articles

    def save_to_parquet(self, articles: list[Article], filename: str = 'sep_articles.parquet'):
        if not articles:
            logger.warning('No articles to save')
            return

        # Convert articles to dictionary format
        data = []
        for article in articles:
            data.append(
                {
                    'title': article.title,
                    'url': article.url,
                    'author': article.author,
                    'first_published': article.first_published,
                    'substantive_revision': article.substantive_revision,
                    'content_html': article.content_html,
                    'content_markdown': article.content_markdown,
                    'word_count': article.word_count,
                    'scraped_at': article.scraped_at,
                }
            )

        df = pd.DataFrame(data)
        df.to_parquet(filename, index=False, compression='snappy')
        logger.info(f'Saved {len(articles)} articles to {filename}')

    def save_markdown_files(self, articles: list[Article], output_dir: str = 'sep_articles'):
        output_path = pathlib.Path(output_dir)
        output_path.mkdir(exist_ok=True)

        for article in articles:
            if article.title:
                # Create safe filename
                safe_title = re.sub(r'[^\w\s-]', '', article.title)
                safe_title = re.sub(r'[-\s]+', '-', safe_title)
                filename = f'{safe_title}.md'

                filepath = output_path / filename

                # Create markdown content with metadata header
                markdown_content = f"""---
title: "{article.title}"
author: "{article.author}"
first_published: "{article.first_published}"
substantive_revision: "{article.substantive_revision}"
url: "{article.url}"
word_count: {article.word_count}
scraped_at: "{article.scraped_at}"
---

# {article.title}

{article.content_markdown}
"""

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

        logger.info(f'Saved {len(articles)} markdown files to {output_dir}/')


def main():
    scraper = SepScraper(delay=1.0)

    # For testing, limit to first 10 articles
    # Remove max_articles parameter for full scrape
    articles = scraper.scrape_all_articles(max_articles=10)

    if articles:
        scraper.save_to_parquet(articles, 'stanford_encyclopedia_articles.parquet')

        scraper.save_markdown_files(articles, 'sep_markdown_files')

        logger.info('Scraping completed!')
        logger.info(f'Total articles: {len(articles)}')
        logger.info(f'Articles with titles: {sum(1 for a in articles if a.title)}')
        logger.info(f'Articles with authors: {sum(1 for a in articles if a.author)}')

        # Display sample of the data
        df = pd.DataFrame(
            [{'title': a.title[:50] + '...' if len(a.title) > 50 else a.title, 'author': a.author, 'word_count': a.word_count, 'first_published': a.first_published} for a in articles[:5]]
        )

        print('\nSample of scraped articles:')
        print(df.to_string(index=False))

    else:
        logger.error('No articles were scraped successfully')


if __name__ == '__main__':
    main()
