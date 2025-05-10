from fastapi import FastAPI, Response
import yfinance as yf
from datetime import datetime
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import io
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    ListItem,
    ListFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

load_dotenv()
app = FastAPI()

symbol_map = ["^NSEI", "^BSESN", "^CRSLDX", "^NSEBANK", "^CNXIT", "^NSEMDCP50"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Index name mapping
index_names = {
    "^NSEI": "NIFTY 50",
    "^BSESN": "SENSEX",
    "^CRSLDX": "CRSLDX",
    "^NSEBANK": "BANK NIFTY",
    "^CNXIT": "NIFTY IT",
    "^NSEMDCP50": "NIFTY Midcap 50",
}


def fetch_market_data():
    """
    Fetch market data for all symbols in symbol_map
    """
    market_data = {}

    # Add metadata
    now = datetime.now()
    market_data["_meta"] = {
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": now.strftime("%H:%M:%S"),
    }

    # Fetch data for each symbol
    for symbol in symbol_map:
        try:
            data = yf.Ticker(symbol)
            history = data.history(period="2d")

            if len(history) >= 2:
                prev_close = history.iloc[-2]["Close"]
                current = history.iloc[-1]

                # Calculate change
                change = current["Close"] - prev_close
                change_percent = (change / prev_close) * 100

                market_data[symbol] = {
                    "Open": round(current["Open"], 2),
                    "High": round(current["High"], 2),
                    "Low": round(current["Low"], 2),
                    "Close": round(current["Close"], 2),
                    "Change": round(change, 2),
                    "Change%": round(change_percent, 2),
                    "PrevClose": round(prev_close, 2),
                }
            else:
                logger.warning(f"Insufficient data for {symbol}")
                market_data[symbol] = {"Error": "Insufficient data"}
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            market_data[symbol] = {"Error": str(e)}

    return market_data


def generate_concise_insights(market_data, sentence_count=6):
    """
    Generate insights using Gemini API in exactly 5-6 sentences
    """
    # Prepare readable data, only for indices
    readable_text = ""

    for symbol, data in market_data.items():
        if symbol != "_meta" and "Open" in data:
            index_name = index_names.get(symbol, symbol)
            readable_text += (
                f"{index_name}: Open={data['Open']}, High={data['High']}, "
                f"Low={data['Low']}, Close={data['Close']}, "
                f"Change={data['Change']} ({data['Change%']}%)\n"
            )

    # Prompt that specifically asks for 5-6 sentences
    prompt = f"""As a professional financial analyst, provide a comprehensive analysis of the Indian market indices in exactly {sentence_count} sentences. 
Use this data for your analysis:

{readable_text}

Your analysis should cover:
1. Overall market sentiment and major index movements
2. Sector-specific performance (IT, Banking, etc.)
3. Key factors influencing today's market
4. Notable outliers or significant data points
5. Brief market outlook based on today's performance
6.See the answer will be in 5 to 6 points
"""

    try:
        # Initialize Gemini model
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Generate response
        response = model.generate_content(prompt)
        insights_text = response.text.strip()

        return insights_text

    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return "Market analysis unavailable at this time."


@app.get("/generate-report")
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
