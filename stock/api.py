from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
import logging
import os
from datetime import datetime
import time
from news_highlights import NewsHighlightsGenerator
from macro import fetch_all_financial_indicators, FinancialDashboard
from pdf_generator import IndianStockMarketPDFGenerator

# Import our market data scraper with the updated functions
from sector_fii_scraper import (
    MarketDataScraper,
    generate_sector_insights,
    generate_institutional_insights,
)
from technical_snapshot import get_market_technical_snapshot
from market_overview import (
    fetch_market_data,
    generate_concise_insights,
)
from top_performers import MarketPerformerScraper
from market_analysis import MarketAnalysisGenerator

# from pdf_generator import generate_pdf_report
from report_generator import cleanup_old_files, generate_pdf_report_individual

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("market_api.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Market Data API")

# Create a temporary directory for PDFs if it doesn't exist
PDF_DIR = os.path.join(os.path.dirname(__file__), "temp_pdfs")
os.makedirs(PDF_DIR, exist_ok=True)


@app.get("/api/sector-fii-data")
async def get_market_data():
    """Get market data including sector-wise movement and institutional activity with separate insights."""
    try:
        # Initialize scraper
        scraper = MarketDataScraper()

        # Scrape sector data
        logger.info("Scraping sector-wise movement data")
        sector_data = scraper.scrape_sector_data()
        logger.info(f"Found {len(sector_data)} sectors")

        # Scrape institutional data
        logger.info("Scraping institutional activity data")
        institutional_data = scraper.scrape_institutional_data()

        logger.info("Generating sector-specific insights")
        sector_insights = generate_sector_insights(sector_data)

        logger.info("Generating institutional activity insights")
        institutional_insights = generate_institutional_insights(institutional_data)

        # Prepare final JSON output with separate insights
        output_data = {
            "sector_movement": {
                "data": sector_data,
                "insight": sector_insights,
            },
            "institutional_activity": {
                "data": institutional_data,
                "insight": institutional_insights,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return JSONResponse(content=output_data)

    except Exception as e:
        logger.error(f"Error generating market data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error generating market data: {str(e)}"
        )


@app.get("/api/news-highlights")
async def get_news_highlights():
    """API endpoint to get financial news highlights."""
    try:
        # Generate fresh news highlights
        generator = NewsHighlightsGenerator()
        news_highlights = generator.get_news_highlights()

        return JSONResponse(content=news_highlights)

    except Exception as e:
        logger.error(f"Error serving news highlights: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to retrieve news highlights",
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.get("/api/indicators", response_model=FinancialDashboard)
def get_all_indicators():
    """Get all financial indicators"""
    try:
        # Call the consolidated function to get all indicators
        indicators = fetch_all_financial_indicators()

        # Return formatted response
        return FinancialDashboard(
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            indicators=indicators,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching indicators: {str(e)}"
        )


@app.get("/market-snapshot", response_class=JSONResponse)
async def market_snapshot():
    try:
        data = get_market_technical_snapshot()
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/market-overview", response_class=JSONResponse)
def generate_report():
    """
    Generate a complete market report (includes all data with detailed insights)
    """
    all_data = fetch_market_data()
    insights = generate_concise_insights(all_data)

    return {
        "date": all_data["_meta"]["date"],
        "timestamp": all_data["_meta"]["timestamp"],
        "market_data": all_data,
        "insights": insights,
    }


@app.get("/api/top-performers")
async def get_market_report():
    try:
        # Scrape data
        scraper = MarketPerformerScraper()
        logger.info("Scraping market data for API report...")
        market_data = scraper.run_full_scrape()

        # Format output
        output_data = {
            "top_performers": {
                "top_gainers": market_data.get("top_gainers", []),
                "top_losers": market_data.get("top_losers", []),
                "insight": market_data.get("insights", "No insights available"),
            }
        }

        return output_data

    except Exception as e:
        logger.error(f"Error generating market report: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.get("/api/comprehensive-market-data")
async def get_comprehensive_market_data():
    """
    Comprehensive endpoint that aggregates all market data sources into a single API response.
    Returns consolidated information from all available endpoints including:
    - Market Analysis (NEW)
    - Sector and FII data
    - News highlights
    - Financial indicators
    - Market technical snapshot
    - Market overview
    - Top performers
    - Summary (NEW)
    """
    try:
        logger.info("Generating comprehensive market data report")
        result = {}

        # Get sector and FII data
        try:
            logger.info("Fetching sector and FII data")
            scraper = MarketDataScraper()
            sector_data = scraper.scrape_sector_data()
            institutional_data = scraper.scrape_institutional_data()
            sector_insights = generate_sector_insights(sector_data)
            institutional_insights = generate_institutional_insights(institutional_data)

            result["sector_and_fii"] = {
                "sector_movement": {
                    "data": sector_data,
                    "insight": sector_insights,
                },
                "institutional_activity": {
                    "data": institutional_data,
                    "insight": institutional_insights,
                },
            }
        except Exception as e:
            logger.error(f"Error fetching sector and FII data: {str(e)}")
            result["sector_and_fii"] = {"error": str(e)}

        # Get news highlights
        try:
            logger.info("Fetching news highlights")
            generator = NewsHighlightsGenerator()
            result["news_highlights"] = generator.get_news_highlights()
        except Exception as e:
            logger.error(f"Error fetching news highlights: {str(e)}")
            result["news_highlights"] = {"error": str(e)}

        # Get financial indicators
        try:
            logger.info("Fetching financial indicators")
            indicators_data = fetch_all_financial_indicators()

            # Convert IndicatorData objects to plain dictionaries
            indicators_dict = {}
            for key, indicator in indicators_data.items():
                if hasattr(indicator, "dict"):
                    # This is a Pydantic model with a dict() method
                    indicators_dict[key] = indicator.dict()
                elif hasattr(indicator, "__dict__"):
                    # This is a regular class with __dict__
                    indicators_dict[key] = indicator.__dict__
                else:
                    # If it's already a dict or other primitive type
                    indicators_dict[key] = indicator

            result["financial_indicators"] = {"indicators": indicators_dict}
        except Exception as e:
            logger.error(f"Error fetching financial indicators: {str(e)}")
            result["financial_indicators"] = {"error": str(e)}

        # Get market technical snapshot
        try:
            logger.info("Fetching market technical snapshot")
            result["market_snapshot"] = get_market_technical_snapshot()
        except Exception as e:
            logger.error(f"Error fetching market technical snapshot: {str(e)}")
            result["market_snapshot"] = {"error": str(e)}

        # Get market overview
        try:
            logger.info("Fetching market overview")
            market_data = fetch_market_data()
            insights = generate_concise_insights(market_data)
            result["market_overview"] = {
                "market_data": market_data,
                "insights": insights,
            }
        except Exception as e:
            logger.error(f"Error fetching market overview: {str(e)}")
            result["market_overview"] = {"error": str(e)}

        # Get top performers
        try:
            logger.info("Fetching top performers")
            scraper = MarketPerformerScraper()
            market_performers_data = scraper.run_full_scrape()
            result["top_performers"] = {
                "top_gainers": market_performers_data.get("top_gainers", []),
                "top_losers": market_performers_data.get("top_losers", []),
                "insight": market_performers_data.get(
                    "insights", "No insights available"
                ),
            }
        except Exception as e:
            logger.error(f"Error fetching top performers: {str(e)}")
            result["top_performers"] = {"error": str(e)}

        # Create a temporary copy of results before adding analysis and summary
        # This will be what we pass to the analysis generator
        temp_result = result.copy()

        # Add metadata
        temp_result["_meta"] = {
            "timestamp": datetime.now().isoformat(),
            "generation_status": "in_progress",
        }

        # Create final result structure first
        final_result = {}

        # Get API key from environment variables
        google_api_key = os.getenv("GOOGLE_API_KEY")

        # Generate Market Analysis (NEW) - add at the beginning
        try:
            if not google_api_key:
                logger.warning("GOOGLE_API_KEY not found in environment variables")
                raise ValueError("GOOGLE_API_KEY is required for Gemini analysis")

            logger.info("Generating market analysis using Gemini")
            analyzer = MarketAnalysisGenerator(api_key=google_api_key)
            market_analysis = analyzer.generate_market_analysis(temp_result)

            # Create the new analysis section first in the result
            final_result["market_analysis"] = {
                "analysis": market_analysis,
                "timestamp": datetime.now().isoformat(),
            }

            # Remember the analyzer for summary generation later
            analysis_successful = True

        except Exception as e:
            logger.error(f"Error generating market analysis: {str(e)}")
            final_result["market_analysis"] = {"error": str(e)}
            analysis_successful = False

        # Add all the existing data sections
        final_result.update(result)

        # Generate Summary (NEW) - add at the end
        try:
            if not analysis_successful:
                raise ValueError("Cannot generate summary without successful analysis")

            logger.info("Generating market summary using Gemini")
            # Use the analysis we just generated
            market_analysis = final_result.get("market_analysis", {}).get(
                "analysis", ""
            )
            summary = analyzer.generate_market_summary(temp_result, market_analysis)

            # Add the summary section at the end
            final_result["summary"] = {
                "content": summary,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error generating market summary: {str(e)}")
            final_result["summary"] = {"error": str(e)}

        # Update metadata to show completion
        final_result["_meta"] = {
            "timestamp": datetime.now().isoformat(),
            "generation_status": "complete",
        }

        logger.info(
            "Successfully generated comprehensive market data with analysis and summary"
        )
        return final_result  # FastAPI will automatically convert this to JSON response

    except Exception as e:
        logger.error(
            f"Error generating comprehensive market data: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error generating comprehensive market data: {str(e)}",
        )


# Define PDF deletion background task
def delete_file_after_delay(file_path: str, delay: int = 10):
    """Delete file after a specified delay in seconds"""
    time.sleep(delay)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Successfully deleted file: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")


@app.get("/api/market-report-pdf")
async def get_market_report_pdf(background_tasks: BackgroundTasks):
    """
    Generate a PDF report of the comprehensive market data.
    Returns the PDF file for download and automatically deletes it from the server after download.
    """
    try:
        logger.info("Generating market report PDF")

        # Step 1: Get comprehensive market data from existing endpoint
        try:
            # This should be the function that your existing endpoint uses to gather all the data
            # You'll need to extract this code from your current endpoint
            logger.info("Fetching comprehensive market data")

            # Instead of calling the endpoint directly, we'll use the same logic
            # to generate the data (reuse the existing functions)
            result = {}

            # Get sector and FII data
            try:
                logger.info("Fetching sector and FII data")
                scraper = MarketDataScraper()
                sector_data = scraper.scrape_sector_data()
                institutional_data = scraper.scrape_institutional_data()
                sector_insights = generate_sector_insights(sector_data)
                institutional_insights = generate_institutional_insights(
                    institutional_data
                )

                result["sector_and_fii"] = {
                    "sector_movement": {
                        "data": sector_data,
                        "insight": sector_insights,
                    },
                    "institutional_activity": {
                        "data": institutional_data,
                        "insight": institutional_insights,
                    },
                }
            except Exception as e:
                logger.error(f"Error fetching sector and FII data: {str(e)}")
                result["sector_and_fii"] = {"error": str(e)}

            # Get news highlights
            try:
                logger.info("Fetching news highlights")
                generator = NewsHighlightsGenerator()
                result["news_highlights"] = generator.get_news_highlights()
            except Exception as e:
                logger.error(f"Error fetching news highlights: {str(e)}")
                result["news_highlights"] = {"error": str(e)}

            # Get financial indicators
            try:
                logger.info("Fetching financial indicators")
                indicators_data = fetch_all_financial_indicators()

                # Convert IndicatorData objects to plain dictionaries
                indicators_dict = {}
                for key, indicator in indicators_data.items():
                    if hasattr(indicator, "dict"):
                        indicators_dict[key] = indicator.dict()
                    elif hasattr(indicator, "__dict__"):
                        indicators_dict[key] = indicator.__dict__
                    else:
                        indicators_dict[key] = indicator

                result["financial_indicators"] = {"indicators": indicators_dict}
            except Exception as e:
                logger.error(f"Error fetching financial indicators: {str(e)}")
                result["financial_indicators"] = {"error": str(e)}

            # Get market technical snapshot
            try:
                logger.info("Fetching market technical snapshot")
                result["market_snapshot"] = get_market_technical_snapshot()
            except Exception as e:
                logger.error(f"Error fetching market technical snapshot: {str(e)}")
                result["market_snapshot"] = {"error": str(e)}

            # Get market overview
            try:
                logger.info("Fetching market overview")
                market_data = fetch_market_data()
                insights = generate_concise_insights(market_data)
                result["market_overview"] = {
                    "market_data": market_data,
                    "insights": insights,
                }
            except Exception as e:
                logger.error(f"Error fetching market overview: {str(e)}")
                result["market_overview"] = {"error": str(e)}

            # Get top performers
            try:
                logger.info("Fetching top performers")
                scraper = MarketPerformerScraper()
                market_performers_data = scraper.run_full_scrape()
                result["top_performers"] = {
                    "top_gainers": market_performers_data.get("top_gainers", []),
                    "top_losers": market_performers_data.get("top_losers", []),
                    "insight": market_performers_data.get(
                        "insights", "No insights available"
                    ),
                }
            except Exception as e:
                logger.error(f"Error fetching top performers: {str(e)}")
                result["top_performers"] = {"error": str(e)}

            # Create a temporary copy of results before adding analysis and summary
            temp_result = result.copy()

            # Add metadata
            temp_result["_meta"] = {
                "timestamp": datetime.now().isoformat(),
                "generation_status": "in_progress",
            }

            # Create final result structure first
            final_result = {}

            # Get API key from environment variables
            google_api_key = os.getenv("GOOGLE_API_KEY")

            # Generate Market Analysis (NEW) - add at the beginning
            try:
                if not google_api_key:
                    logger.warning("GOOGLE_API_KEY not found in environment variables")
                    raise ValueError("GOOGLE_API_KEY is required for Gemini analysis")

                logger.info("Generating market analysis using Gemini")
                analyzer = MarketAnalysisGenerator(api_key=google_api_key)
                market_analysis = analyzer.generate_market_analysis(temp_result)

                # Create the new analysis section first in the result
                final_result["market_analysis"] = {
                    "analysis": market_analysis,
                    "timestamp": datetime.now().isoformat(),
                }

                # Remember the analyzer for summary generation later
                analysis_successful = True

            except Exception as e:
                logger.error(f"Error generating market analysis: {str(e)}")
                final_result["market_analysis"] = {"error": str(e)}
                analysis_successful = False

            # Add all the existing data sections
            final_result.update(result)

            # Generate Summary (NEW) - add at the end
            try:
                if not analysis_successful:
                    raise ValueError(
                        "Cannot generate summary without successful analysis"
                    )

                logger.info("Generating market summary using Gemini")
                # Use the analysis we just generated
                market_analysis = final_result.get("market_analysis", {}).get(
                    "analysis", ""
                )
                summary = analyzer.generate_market_summary(temp_result, market_analysis)

                # Add the summary section at the end
                final_result["summary"] = {
                    "content": summary,
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                logger.error(f"Error generating market summary: {str(e)}")
                final_result["summary"] = {"error": str(e)}

            # Update metadata to show completion
            final_result["_meta"] = {
                "timestamp": datetime.now().isoformat(),
                "generation_status": "complete",
            }

            market_data = final_result

        except Exception as e:
            logger.error(f"Error fetching comprehensive market data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching comprehensive market data: {str(e)}",
            )

        # Step 2: Generate PDF using the market data
        try:
            logger.info("Generating PDF from market data")
            pdf_generator = IndianStockMarketPDFGenerator(output_dir="temp_reports")
            pdf_file_path = pdf_generator.generate_pdf(market_data)
            logger.info(f"Generated PDF file at: {pdf_file_path}")
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating PDF: {str(e)}",
            )

        # Step 3: Return the PDF file and schedule it for deletion
        if os.path.exists(pdf_file_path):
            logger.info(f"Returning PDF file and scheduling deletion")

            # Schedule deletion after download (with a delay to ensure complete download)
            background_tasks.add_task(delete_file_after_delay, pdf_file_path, 60)

            # Generate a user-friendly filename
            date_str = datetime.now().strftime("%d_%b_%Y")
            filename = f"Indian_Stock_Market_Report_{date_str}.pdf"

            # Return the file with appropriate headers
            return FileResponse(
                path=pdf_file_path,
                filename=filename,
                media_type="application/pdf",
                background=background_tasks,
            )
        else:
            logger.error("Generated PDF file not found")
            raise HTTPException(
                status_code=500,
                detail="Generated PDF file not found",
            )

    except Exception as e:
        logger.error(f"Error generating market report PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating market report PDF: {str(e)}",
        )


# Run the app with uvicorn when the file is executed directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8009, reload=False)
