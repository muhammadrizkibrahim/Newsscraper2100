import logging
import re
from datetime import date
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .basescraper import BaseScraper


class DetikScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "https://www.detik.com"
        self.start_date = start_date
        self.continue_scraping = True

    async def build_search_url(self, keyword, page):
        query_params = {
            "query": keyword,
            "page": page,
            "result_type": "relevansi",
        }
        url = f"{self.base_url}/search/searchall?{urlencode(query_params)}"
        return await self.fetch(url)

    def parse_article_links(self, response_text):
        soup = BeautifulSoup(response_text, "html.parser")

        # Cari semua article items
        articles = soup.select(".list-content__item")
        if not articles:
            logging.warning("No articles found")
            return None

        filtered_hrefs = set()

        for article in articles:
            # Ambil link dari h3 title (lebih spesifik)
            title_link = article.select_one("h3.media__title a")

            if title_link and title_link.get("href"):
                href = title_link.get("href")

                # Filter out unwanted content
                if all(
                    x not in href
                    for x in [
                        "wolipop.detik.com",
                        "/detiktv/",
                        "/pop/",
                        "20.detik.com",  # Video content
                        "/foto-",  # Photo galleries
                        "-video",
                    ]
                ):
                    filtered_hrefs.add(href)

        logging.info(f"Found {len(filtered_hrefs)} valid article links")
        return filtered_hrefs if filtered_hrefs else None

    async def get_article(self, link, keyword):
        # Tambahkan ?single=1 untuk format lebih sederhana
        response_text = await self.fetch(f"{link}?single=1")
        if not response_text:
            logging.warning(f"No response for {link}")
            return

        soup = BeautifulSoup(response_text, "html.parser")

        try:
            # Coba berbagai selector untuk adaptasi struktur berbeda

            # Category
            category = None
            breadcrumb = soup.select_one(".page__breadcrumb a, .breadcrumb a")
            if breadcrumb:
                category = breadcrumb.get_text(strip=True)

            # Title - coba beberapa kemungkinan selector
            title = None
            for selector in [".detail__title", "h1.detail__title", "h1"]:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break

            if not title:
                logging.error(f"No title found for {link}")
                return

            # Author
            author = "Unknown"
            author_elem = soup.select_one(".detail__author, .author")
            if author_elem:
                author = author_elem.get_text(strip=True)

            # Publish date
            publish_date_str = None
            for selector in [".detail__date", ".date", "time"]:
                date_elem = soup.select_one(selector)
                if date_elem:
                    publish_date_str = date_elem.get_text(strip=True)
                    break

            if not publish_date_str:
                logging.warning(f"No date found for {link}")
                return

            # Content - coba beberapa selector
            content = None
            for selector in [
                ".detail__body-text",
                ".itp_bodycontent",
                ".detail-content",
            ]:
                content_div = soup.select_one(selector)
                if content_div:
                    # Clone untuk tidak mengubah DOM asli
                    content_copy = content_div

                    # Remove unwanted elements - lebih lengkap
                    unwanted_selectors = [
                        "script",
                        "style",
                        "iframe",
                        "ins",  # Tags standar
                        ".noncontent",
                        ".linksisip",  # Detik specific
                        ".parallaxindetail",
                        ".staticdetail_container",  # Ads containers
                        ".aevp",
                        ".pip-vid",  # Video embeds
                        '[data-type="_mgwidget"]',  # MGID widgets
                        ".eyeo",
                        "template",  # MGID templates
                        ".detail__body-tag",  # Tags section
                        "table.linksisip",  # Link tables
                        'div[id^="div-gpt-ad"]',  # Google ads
                        'div[id^="mgw"]',  # MGID widgets
                        "div[data-tf-live]",  # Typeform
                    ]

                    for selector_to_remove in unwanted_selectors:
                        for tag in content_copy.select(selector_to_remove):
                            tag.extract()

                    # Remove tags dengan class tertentu
                    for tag in content_copy.find_all(True):
                        classes = tag.get("class", [])
                        if any(
                            cls in ["clearfix", "ads-", "mg_", "mc", "para_caption"]
                            for cls in classes
                        ):
                            tag.extract()

                    # Remove comment tags
                    for comment in content_copy.find_all(
                        string=lambda text: isinstance(text, str) and "<!--" in text
                    ):
                        comment.extract()

                    # Ambil semua paragraf dan strong tags
                    paragraphs = []
                    for elem in content_copy.find_all(["p", "strong"]):
                        text = elem.get_text(strip=True)
                        # Skip empty paragraphs dan paragraphs yang hanya berisi "ADVERTISEMENT" dll
                        if text and text not in [
                            "ADVERTISEMENT",
                            "SCROLL TO CONTINUE WITH CONTENT",
                        ]:
                            paragraphs.append(text)

                    if paragraphs:
                        content = "\n\n".join(paragraphs)
                    else:
                        # Fallback: ambil semua text
                        content = content_copy.get_text(separator="\n", strip=True)
                        # Clean up multiple newlines
                        content = "\n\n".join(
                            [
                                line.strip()
                                for line in content.split("\n")
                                if line.strip()
                            ]
                        )
                    break

            if not content:
                logging.warning(f"No content found for {link}")
                return

            # Parse date
            publish_date = self.parse_date(publish_date_str)
            if not publish_date:
                logging.error(
                    f"Error parsing date '{publish_date_str}' for article {link}"
                )
                return

            # Check date filter
            if self.start_date and publish_date < self.start_date:
                logging.info(
                    f"Article date {publish_date} is before start_date {self.start_date}, stopping"
                )
                self.continue_scraping = False
                return

            item = {
                "title": title,
                "publish_date": publish_date,
                "author": author,
                "content": content,
                "keyword": keyword,
                "category": category or "Unknown",
                "source": self.base_url.split("www.")[1],
                "link": link,
            }

            await self.queue_.put(item)
            logging.info(f"Successfully scraped: {title}")

        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}", exc_info=True)
