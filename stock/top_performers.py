import os
import json
import logging
import re
from datetime import datetime
import time
from typing import Dict, List, Any

# Langchain imports
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Third party imports
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("market_data.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Only use Trendlyne URLs for gainers and losers
TRENDLYNE_GAINERS_URL = (
    "https://trendlyne.com/stock-screeners/price-based/top-gainers/today/"
)
TRENDLYNE_LOSERS_URL = (
    "https://trendlyne.com/stock-screeners/price-based/top-losers/today/"
)

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class MarketPerformerScraper:
    """Class to scrape market data from Trendlyne and generate insights with Gemini"""

    def __init__(self):
        """Initialize the scraper"""
        self.gemini_llm = None
        if GEMINI_API_KEY:
            try:
                # Updated to use the correct model name - check if it's "gemini-1.5-pro" instead
                self.gemini_llm = GoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=GEMINI_API_KEY,
                    temperature=0.2,
                    max_output_tokens=1024,
                )
                logger.info("Successfully initialized Gemini API")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {str(e)}")
                # Fallback to another model if needed
                try:
                    self.gemini_llm = GoogleGenerativeAI(
                        model="gemini-1.0-pro",
                        google_api_key=GEMINI_API_KEY,
                        temperature=0.2,
                        max_output_tokens=1024,
                    )
                    logger.info(
                        "Successfully initialized Gemini API with fallback model"
                    )
                except Exception as e2:
                    logger.warning(
                        f"Failed to initialize fallback Gemini model: {str(e2)}"
                    )
        else:
            logger.warning(
                "Gemini API key not found. Insights generation will be skipped."
            )

    def get_chrome_driver(self):
        """Set up and return a Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def _parse_price_change(self, text):
        """Parse price change text that contains value and percentage"""
        try:
            # Handle the format like "33.93 (20.0%)" or "-1.24 (-12.4%)"
            match = re.match(r"([-\d.]+)\s+\(([-\d.]+)%?\)", text)
            if match:
                return float(match.group(1))
            # Try direct conversion if no pattern match
            return float(
                text.replace("INR", "").replace(",", "").replace("%", "").strip()
            )
        except Exception as e:
            logger.debug(f"Error parsing price change '{text}': {str(e)}")
            return 0.0

    def _parse_percentage_change(self, text):
        """Parse percentage change text that contains value and percentage"""
        try:
            # Handle the format like "33.93 (20.0%)" or "-1.24 (-12.4%)"
            match = re.match(r"([-\d.]+)\s+\(([-\d.]+)%?\)", text)
            if match:
                return float(match.group(2))
            # Check if it's just a percentage
            if "%" in text:
                return float(text.replace("%", "").strip())
            return float(text)
        except Exception as e:
            logger.debug(f"Error parsing percentage '{text}': {str(e)}")
            return 0.0

    def scrape_trendlyne_data(self, url):
        """Scrape stock data from a Trendlyne URL"""
        driver = self.get_chrome_driver()

        try:
            # Load the URL
            logger.info(f"Loading URL: {url}")
            driver.get(url)

            # Wait for JavaScript to load content
            time.sleep(8)  # Increased wait time

            # Get the page source
            page_source = driver.page_source

            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")

            # Find the table with stock data
            table = soup.find("table", class_="table")

            if not table:
                logger.error("Could not find table with stock data")
                return []

            # Extract headers
            headers = []
            header_row = table.find("thead").find("tr")
            for th in header_row.find_all("th"):
                headers.append(th.text.strip())

            # Extract data rows (limited to top 10)
            stocks = []
            tbody = table.find("tbody")
            if tbody:
                count = 0
                for tr in tbody.find_all("tr"):
                    if count >= 10:  # Limit to top 10
                        break

                    row_data = {}
                    for i, td in enumerate(tr.find_all("td")):
                        if i < len(headers):
                            row_data[headers[i]] = td.text.strip()

                    # Debug: log raw row data
                    logger.debug(f"Raw row data: {row_data}")

                    # Convert data to our standardized format
                    try:
                        # Get company name from first column
                        company_name = row_data.get(
                            "Name", row_data.get(headers[0], "")
                        )

                        # Find current price (LTP or Last Price)
                        price_key = next(
                            (
                                h
                                for h in row_data.keys()
                                if any(term in h for term in ["LTP", "Price", "Last"])
                            ),
                            None,
                        )
                        if not price_key and headers:
                            price_key = headers[1]  # Fallback to second column

                        price_text = row_data.get(price_key, "0")
                        current_price = float(
                            price_text.replace("INR", "").replace(",", "").strip()
                        )

                        # Find change column
                        change_key = next(
                            (
                                h
                                for h in row_data.keys()
                                if "Change(%)" in h or "Change %" in h
                            ),
                            None,
                        )
                        if not change_key:
                            change_key = next(
                                (h for h in row_data.keys() if "Change" in h), None
                            )

                        if change_key:
                            change_text = row_data.get(change_key, "0 (0%)")
                            price_change = self._parse_price_change(change_text)
                            percentage_change = self._parse_percentage_change(
                                change_text
                            )
                        else:
                            # Fallback values if we can't find change columns
                            price_change = 0.0
                            percentage_change = 0.0

                        # Add to standardized format
                        stocks.append(
                            {
                                "company_name": company_name,
                                "current_price": current_price,
                                "price_change": price_change,
                                "percentage_change": percentage_change,
                            }
                        )
                        count += 1
                        logger.debug(
                            f"Processed stock: {company_name}, price: {current_price}, change: {price_change}, %: {percentage_change}"
                        )

                    except Exception as e:
                        logger.error(f"Error parsing row data: {str(e)}")
                        logger.error(f"Problematic row: {row_data}")
                        continue

            logger.info(f"Successfully scraped {len(stocks)} stocks from {url}")
            return stocks

        except Exception as e:
            logger.error(f"Error in scrape_trendlyne_data: {str(e)}")
            return []

        finally:
            driver.quit()

    def scrape_top_gainers_losers(self) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape top gainers and losers from Trendlyne"""
        logger.info("Starting to scrape top gainers and losers from Trendlyne")

        # Get top gainers
        top_gainers = self.scrape_trendlyne_data(TRENDLYNE_GAINERS_URL)

        # Get top losers
        top_losers = self.scrape_trendlyne_data(TRENDLYNE_LOSERS_URL)

        # Make sure losers have negative changes
        for loser in top_losers:
            if loser["price_change"] > 0:
                loser["price_change"] = -loser["price_change"]
            if loser["percentage_change"] > 0:
                loser["percentage_change"] = -loser["percentage_change"]

        # Return combined results
        result = {"gainers": top_gainers, "losers": top_losers}

        logger.info(
            f"Completed scraping: {len(top_gainers)} gainers, {len(top_losers)} losers"
        )
        return result

    def generate_market_insights(self, market_data):
        """Generate market insights using Gemini"""
        if not self.gemini_llm:
            return {"error": "Gemini API key not configured or initialization failed"}

        try:
            # Prepare data for analysis
            gainers = market_data.get("top_gainers", [])
            losers = market_data.get("top_losers", [])

            # Create prompt for Gemini with focus on brevity
            prompt_template = PromptTemplate(
                input_variables=["gainers", "losers", "date"],
                template="""
                You are a stock market expert analyzing today's top gainers and losers.
                
                Today's date: {date}
                
                Top Gainers:
                {gainers}
                
                Top Losers:
                {losers}
                
                Based on the above data, provide 3-5 brief bullet points (one sentence each) summarizing:
                1. Overall Stock sentiment
                2. Notable Stock patterns
                3. Key individual stock movements
                4. Mention all the stock which are performing well and not well.
                Keep your entire response to 3-5 concise bullet points only.
                """,
            )

            # Format data for prompt
            gainers_text = (
                "\n".join(
                    [
                        f"- {g['company_name']}: Current price INR{g['current_price']:.2f}, Change: +INR{g['price_change']:.2f} (+{g['percentage_change']:.2f}%)"
                        for g in gainers
                    ]
                )
                if gainers
                else "No data available"
            )

            losers_text = (
                "\n".join(
                    [
                        f"- {l['company_name']}: Current price INR{l['current_price']:.2f}, Change: INR{l['price_change']:.2f} ({l['percentage_change']:.2f}%)"
                        for l in losers
                    ]
                )
                if losers
                else "No data available"
            )

            # Create chain
            chain = LLMChain(llm=self.gemini_llm, prompt=prompt_template)

            # Run chain
            current_date = datetime.now().strftime("%Y-%m-%d")
            insights = chain.run(
                {"gainers": gainers_text, "losers": losers_text, "date": current_date}
            )

            return {"insights": insights}

        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {"error": f"Failed to generate insights: {str(e)}"}

    def run_full_scrape(self):
        """Run complete market data scraping and return combined JSON"""
        try:
            # Timestamp for data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Scrape top gainers and losers
            logger.info("Starting market data scraping...")
            market_movers = self.scrape_top_gainers_losers()

            # Compile market data
            market_data = {
                "timestamp": timestamp,
                "top_gainers": market_movers["gainers"],
                "top_losers": market_movers["losers"],
            }

            # Generate insights if Gemini is configured
            insights_message = "No insights generated"
            if self.gemini_llm:
                logger.info("Generating market insights with Gemini...")
                insights_result = self.generate_market_insights(market_data)

                if "insights" in insights_result:
                    insights_message = insights_result["insights"]
                elif "error" in insights_result:
                    insights_message = (
                        f"Error generating insights: {insights_result['error']}"
                    )
            else:
                insights_message = (
                    "Insights generation skipped - Gemini API key not configured"
                )

            # Add insights to market data
            market_data["insights"] = insights_message

            # Save to JSON file
            output_file = f"market_data_{datetime.now().strftime('%Y%m%d')}.json"
            with open(output_file, "w") as f:
                json.dump(market_data, f, indent=2)

            logger.info(f"Market data saved to {output_file}")
            return market_data

        except Exception as e:
            logger.error(f"Error in market scrape: {str(e)}")
            # Return partial data if available
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
                "top_gainers": [],
                "top_losers": [],
                "insights": "Failed to generate due to error",
            }


# # Example usage
# if __name__ == "__main__":
#     try:
#         scraper = MarketDataScraper()
#         market_data = scraper.run_full_scrape()

#         # Print insights if available
#         print("\n" + "=" * 80)
#         print("MARKET INSIGHTS")
#         print("=" * 80)
#         print(market_data.get("insights", "No insights available"))
#         print("=" * 80)

#         # Print summary
#         print(
#             f"\nScraped {len(market_data.get('top_gainers', []))} gainers and {len(market_data.get('top_losers', []))} losers"
#         )
#         print(
#             f"Full data saved to market_data_{datetime.now().strftime('%Y%m%d')}.json"
#         )
#     except Exception as e:
#         print(f"Fatal error in main execution: {str(e)}")
