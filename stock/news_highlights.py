import json
import time
import logging
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging with simpler format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class FinancialNewsScraper:
    def __init__(self, headless=True, timeout=30):
        """Initialize the scraper with browser options."""
        self.timeout = timeout
        self.setup_driver(headless)
        self.site_selectors = {
            "yahoo_finance": {
                "container": "li.js-stream-content, div.Ov\\(h\\), div.NewsArticle",
                "title": "h3, a[data-test='mega-item-header'], h2 a",
                "summary": "p, div[data-test='story-body'], div.summary",
                "accept_cookies": "button.btn.primary, button[name='agree']",
            },
            "reuters": {
                "container": "div.story-card, article, div.media-story-card",
                "title": "h3.text-heading-label, div.heading, div.media-story-card__heading",
                "summary": "p.text-paragraph, div.standfirst, div.media-story-card__description",
                "accept_cookies": "button#onetrust-accept-btn-handler, button.accept-cookies",
            },
            "cnbc": {
                "container": "div.Card-standardBreakerCard, div.Card, div.SearchResult-searchResult",
                "title": "a.Card-title, div.Card-titleContainer, div.SearchResult-searchResultTitle",
                "summary": "div.Card-description, p, div.SearchResult-searchResultCard div",
                "accept_cookies": "button#onetrust-accept-btn-handler, button.acceptAllButton",
            },
            "financial_express": {
                "container": "div.stories-card, div.ie-stories, div.article-list, article",
                "title": "h3.title, h4.entry-title a, h2 a, h3 a",
                "summary": "p.excerpt, div.excerpt, p, div.story-short",
                "accept_cookies": "button.consent-btn, button.accept-cookie",
            },
            "default": {
                "container": "article, div.article, div.card, div.post, div.item, div.story, div.news-item, .story-card, .news-card",
                "title": "h1, h2, h3, h4, a.title, div.title, a.headline",
                "summary": "p, div.summary, div.excerpt, div.description, div.content, .synopsis, .summary",
                "accept_cookies": "button#accept-cookies, button.accept-cookies, button.agree, button.accept, button[aria-label='Accept cookies']",
            },
        }

    def setup_driver(self, headless):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument(
            "--disable-features=IsolateOrigins,site-per-process"
        )
        chrome_options.add_argument("--disable-web-security")  # For cross-origin issues
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            logger.info("WebDriver initiated successfully")
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            logger.error(traceback.format_exc())
            raise

    def get_site_config(self, url):
        """Determine which site configuration to use based on URL."""
        if "finance.yahoo.com" in url:
            return self.site_selectors["yahoo_finance"]
        elif "reuters.com" in url:
            return self.site_selectors["reuters"]
        elif "cnbc.com" in url:
            return self.site_selectors["cnbc"]
        elif "financialexpress.com" in url:
            return self.site_selectors["financial_express"]
        else:
            return self.site_selectors["default"]

    def scrape_articles(self, url, num_articles=15, scroll_attempts=5):
        """
        Scrape titles and summaries from financial news pages.

        Args:
            url (str): The URL to scrape
            num_articles (int): Maximum number of articles to scrape
            scroll_attempts (int): Number of times to scroll down to load more content

        Returns:
            list: List of dictionaries containing titles and summaries
        """
        articles = []
        site_config = self.get_site_config(url)
        site_name = self.get_source_name_from_url(url)

        logger.info(f"Starting to scrape {site_name} from {url}")

        try:
            # Try to load the page with extended timeout
            try:
                self.driver.get(url)
                logger.info(f"Page loaded: {site_name}")
            except TimeoutException:
                logger.warning(
                    f"Page load timeout for {site_name}. Trying to proceed anyway."
                )
            except WebDriverException as e:
                logger.error(f"WebDriver error loading {site_name}: {str(e)}")
                return articles

            # Wait for news content to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, site_config["container"].split(", ")[0])
                    )
                )
                logger.info(f"Content containers found for {site_name}")
            except TimeoutException:
                logger.warning(
                    f"Timeout waiting for main content on {site_name}. Attempting to proceed anyway."
                )

            # Accept cookies if prompted and config exists
            if site_config["accept_cookies"]:
                try:
                    cookie_selectors = site_config["accept_cookies"].split(", ")
                    for selector in cookie_selectors:
                        try:
                            cookie_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            cookie_button.click()
                            logger.info(
                                f"Accepted cookies on {site_name} using selector: {selector}"
                            )
                            break
                        except TimeoutException:
                            continue
                        except Exception as e:
                            logger.warning(
                                f"Error clicking cookie button with selector {selector}: {e}"
                            )
                except Exception as e:
                    logger.info(
                        f"No cookie consent popup found or already accepted on {site_name}: {e}"
                    )

            # Scroll to load more articles
            for i in range(scroll_attempts):
                logger.info(
                    f"Scroll attempt {i+1} to load more articles on {site_name}"
                )
                try:
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight * 0.7);"
                    )
                    time.sleep(3)  # Wait time for content to load
                except Exception as e:
                    logger.warning(f"Error scrolling on {site_name}: {e}")

            # Try multiple container selectors
            container_selectors = site_config["container"].split(", ")
            article_containers = []

            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        article_containers.extend(containers)
                        logger.info(
                            f"Found {len(containers)} containers with selector '{selector}' on {site_name}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Error finding containers with selector '{selector}' on {site_name}: {e}"
                    )

            if not article_containers:
                logger.warning(f"Could not find article containers for {site_name}")
                # Fall back to default selectors
                default_selectors = self.site_selectors["default"]["container"].split(
                    ", "
                )
                for selector in default_selectors:
                    try:
                        containers = self.driver.find_elements(
                            By.CSS_SELECTOR, selector
                        )
                        if containers:
                            article_containers.extend(containers)
                            logger.info(
                                f"Found {len(containers)} containers with default selector '{selector}' on {site_name}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error finding containers with default selector '{selector}' on {site_name}: {e}"
                        )

            if not article_containers:
                logger.error(f"No article containers found for {site_name}")
                return articles

            logger.info(
                f"Found {len(article_containers)} potential articles on {site_name}"
            )

            # Process found article containers
            for container in article_containers[:num_articles]:
                try:
                    article = self.extract_article(container, site_config, site_name)
                    if article and article["title"]:  # Only add if we have a title
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Error extracting article from {site_name}: {e}")
                    continue

            logger.info(
                f"Successfully scraped {len(articles)} articles from {site_name}"
            )

        except Exception as e:
            logger.error(f"Error scraping {site_name} ({url}): {e}")
            logger.error(traceback.format_exc())

        return articles

    def extract_article(self, container, site_config, site_name):
        """Extract title and summary from an article container."""
        try:
            # Extract title using multiple possible selectors
            title = ""
            title_selectors = site_config["title"].split(", ")

            for selector in title_selectors:
                try:
                    title_elem = container.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue

            # If no title found, try default selectors
            if not title:
                default_title_selectors = self.site_selectors["default"]["title"].split(
                    ", "
                )
                for selector in default_title_selectors:
                    try:
                        title_elem = container.find_element(By.CSS_SELECTOR, selector)
                        title = title_elem.text.strip()
                        if title:
                            break
                    except:
                        continue

            if not title:
                return None

            # Extract summary using multiple possible selectors
            summary = ""
            summary_selectors = site_config["summary"].split(", ")

            for selector in summary_selectors:
                try:
                    summary_elem = container.find_element(By.CSS_SELECTOR, selector)
                    summary = summary_elem.text.strip()
                    if summary and len(summary) > 15:  # Minimum sensible length
                        break
                except:
                    continue

            # If no summary found with primary selectors, try default selectors
            if not summary:
                default_summary_selectors = self.site_selectors["default"][
                    "summary"
                ].split(", ")
                for selector in default_summary_selectors:
                    try:
                        summary_elems = container.find_elements(
                            By.CSS_SELECTOR, selector
                        )
                        for elem in summary_elems:
                            text = elem.text.strip()
                            if text and len(text) > 15:  # Minimum sensible length
                                summary = text
                                break
                        if summary:
                            break
                    except:
                        continue

            article = {
                "title": title,
                "summary": summary if summary else "No summary available",
                "source": site_name,
            }

            logger.info(f"Extracted article from {site_name}: {title[:50]}...")
            return article

        except Exception as e:
            logger.warning(f"Error extracting article from {site_name}: {e}")
            return None

    def get_source_name_from_url(self, url):
        """Extract a readable source name from URL."""
        if "finance.yahoo.com" in url:
            return "Yahoo Finance"
        elif "reuters.com" in url:
            return "Reuters"
        elif "cnbc.com" in url:
            return "CNBC"
        elif "financialexpress.com" in url:
            return "Financial Express"
        else:
            return "Unknown Source"

    def close(self):
        """Close the WebDriver session."""
        if hasattr(self, "driver"):
            try:
                self.driver.quit()
                logger.info("WebDriver session closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")


class SimpleNewsClassifier:
    """A simple classifier that relies on keyword matching"""

    def __init__(self):
        self.impact_keywords = [
            "policy",
            "regulation",
            "economy",
            "inflation",
            "recession",
            "central bank",
            "fed",
            "federal reserve",
            "interest rate",
            "gdp",
            "treasury",
            "economic growth",
            "fiscal",
            "monetary",
            "budget",
            "minister",
            "government",
            "tax",
            "deficit",
            "stimulus",
            "debt",
            "tariff",
            "market crash",
            "rally",
            "volatility",
            "crisis",
            "emergency",
            "warning",
            "alert",
            "critical",
            "major",
            "significant",
            "breakthrough",
            "disruption",
            "transformation",
            "revolution",
        ]

        self.india_keywords = [
            "india",
            "indian",
            "mumbai",
            "delhi",
            "bse",
            "nse",
            "sensex",
            "nifty",
            "rupee",
            "rbi",
            "sebi",
            "finance minister",
            "pm modi",
            "government of india",
            "indian economy",
            "indian market",
            "indian stock",
            "indian rupee",
            "indian banks",
            "indian companies",
        ]

        self.global_keywords = [
            "global",
            "world",
            "international",
            "foreign",
            "overseas",
            "europe",
            "asia",
            "america",
            "china",
            "japan",
            "uk",
            "us",
            "european",
            "asian",
            "american",
            "foreign exchange",
            "forex",
            "global market",
            "world economy",
            "international trade",
            "global economy",
            "world market",
        ]

    def categorize_news(self, articles):
        impact_news = []
        india_news = []
        global_news = []

        for article in articles:
            title = article["title"].lower()
            summary = (
                article["summary"].lower()
                if article["summary"] != "No summary available"
                else ""
            )
            source = article["source"]

            # Create bullet point
            bullet = f"{article['title']} (Source: {source})"

            # Check for impact keywords first
            is_impact = any(
                keyword in title or keyword in summary
                for keyword in self.impact_keywords
            )

            # Then check for India/Global keywords
            is_india = any(
                keyword in title or keyword in summary
                for keyword in self.india_keywords
            )
            is_global = any(
                keyword in title or keyword in summary
                for keyword in self.global_keywords
            )

            # Categorize the news
            if is_impact:
                impact_news.append(bullet)
            elif is_india:
                india_news.append(bullet)
            elif is_global:
                global_news.append(bullet)
            else:
                # If no specific category matches, default to impact if it's from a major source
                if source in ["Reuters", "CNBC", "Financial Express"]:
                    impact_news.append(bullet)
                else:
                    global_news.append(bullet)

        # Limit to 7 articles per category
        return {
            "impact": impact_news[:7],
            "india": india_news[:7],
            "global": global_news[:7],
        }


class NewsHighlightsGenerator:
    def __init__(self):
        """Initialize the news highlights generator."""
        self.scraper = FinancialNewsScraper(headless=True, timeout=45)
        self.classifier = SimpleNewsClassifier()
        logger.info("Using simple keyword classifier")

    def categorize_news(self, articles):
        """
        Categorize news into Economic Policy and Corporate News.
        """
        if not articles:
            return {
                "economic_policy": ["No articles found to categorize"],
                "corporate_news": ["No articles found to categorize"],
            }

        logger.info("Using simple classifier for categorization")
        return self.classifier.categorize_news(articles)

    def get_news_highlights(self, urls=None):
        """
        Scrape news articles from multiple sources, categorize them, and return highlights.

        Args:
            urls (list): List of URLs to scrape (defaults to successful financial news sites)

        Returns:
            dict: Categorized news highlights
        """
        if urls is None:
            # Only using sources that successfully returned articles based on logs
            urls = [
                "https://www.cnbc.com/finance/",
                "https://www.financialexpress.com/market/",
            ]

        try:
            all_articles = []
            source_stats = {}
            failed_sources = []

            # Scrape articles from each URL with retry mechanism
            for url in urls:
                site_name = self.scraper.get_source_name_from_url(url)
                logger.info(f"Starting scraping from {site_name} ({url})")

                # Try twice with a pause in between if no articles were found the first time
                for attempt in range(1, 3):
                    try:
                        articles = self.scraper.scrape_articles(url, num_articles=20)
                        if articles:
                            source_stats[site_name] = len(articles)
                            all_articles.extend(articles)
                            logger.info(
                                f"Successfully scraped {len(articles)} articles from {site_name} on attempt {attempt}"
                            )
                            break  # Exit retry loop if successful
                        else:
                            logger.warning(
                                f"No articles found from {site_name} on attempt {attempt}"
                            )
                            if (
                                attempt < 2
                            ):  # Only sleep and retry if this is the first attempt
                                time.sleep(5)  # Pause before retry
                    except Exception as e:
                        logger.error(
                            f"Failed to scrape {site_name} on attempt {attempt}: {e}"
                        )
                        if (
                            attempt < 2
                        ):  # Only sleep and retry if this is the first attempt
                            time.sleep(5)  # Pause before retry

                # Record failure if both attempts failed
                if site_name not in source_stats or source_stats[site_name] == 0:
                    source_stats[site_name] = 0
                    failed_sources.append(site_name)

                time.sleep(3)  # Brief pause between sites

            # Check if we have any articles
            if not all_articles:
                logger.error("No articles scraped from any source")
                error_message = f"Failed to scrape any articles. Failed sources: {', '.join(failed_sources)}"
                return {
                    "error": error_message,
                    "timestamp": datetime.now().isoformat(),
                }

            # Log scraping statistics
            logger.info("------- Scraping Statistics -------")
            for source, count in source_stats.items():
                logger.info(f"{source}: {count} articles")
            logger.info(f"Total articles scraped: {len(all_articles)}")

            # Categorize articles
            logger.info("Categorizing articles...")
            categorized_news = self.categorize_news(all_articles)

            # Add timestamp to result
            result = {
                "timestamp": datetime.now().isoformat(),
                "economic_policy": categorized_news.get("economic_policy", []),
                "corporate_news": categorized_news.get("corporate_news", []),
            }

            return result

        except Exception as e:
            logger.error(f"Error generating news highlights: {e}")
            logger.error(traceback.format_exc())
            return {
                "error": f"Failed to retrieve news highlights: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            # Close the scraper
            try:
                self.scraper.close()
            except Exception as e:
                logger.error(f"Error closing scraper: {e}")
