# Made by Vrushabh

import os
import json
import yfinance as yf
import ta
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# --- Load environment variables ---
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")

# --- Setup Gemini Client (Using gemini-2.0-flash) ---
genai.configure(api_key=GEMINI_API_KEY)
gemini_client = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 1024,
    },
)

# --- Constants ---
INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty FMCG": "^CNXFMCG",
}


# --- Utility Functions ---
def get_previous_trading_day():
    today = datetime.now()
    previous_day = today - timedelta(days=1)
    while previous_day.weekday() >= 5:  # Skip Saturday and Sunday
        previous_day -= timedelta(days=1)
    return previous_day.strftime("%B %d, %Y")


def fetch_technical_snapshot():
    """Fetch technical data for Indian indices."""
    snapshot = {}
    for name, symbol in INDICES.items():
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo", interval="1d")
        if hist.empty or len(hist) < 50:
            continue
        close = hist["Close"]
        snapshot[name] = {
            "close": round(close.iloc[-1], 2),
            "support": round(close.tail(20).min(), 2),
            "rsi": round(ta.momentum.RSIIndicator(close=close).rsi().iloc[-1], 2),
            "macd": {
                "line": round(ta.trend.MACD(close=close).macd().iloc[-1], 2),
                "signal": round(ta.trend.MACD(close=close).macd_signal().iloc[-1], 2),
            },
        }
    return snapshot


def generate_insights(snapshot_data: dict):
    """Send snapshot data to Gemini and receive financial insights."""
    prompt = f"""
    You are a professional financial analyst.
    Analyze the following JSON data on Indian stock market indices. Generate 6-7 concise insights.
    
    Guidelines:
    - Each insight must be one sentence maximum
    - Focus on clear market implications
    - Identify key technical patterns and their significance
    - Mention support/resistance levels when relevant
    - Highlight overbought/oversold conditions
    - Note any divergences or unusual patterns
    - Provide actionable insights for traders/investors
    
    Input Data:
    {json.dumps(snapshot_data, indent=2)}
    
    Output:
    - Exactly 6-7 bullet points
    - Each point < 15 words
    - Professional, formal tone
    - No extra explanations
    - Focus on actionable insights
    """

    response = gemini_client.generate_content(prompt)
    insights_text = response.text.strip()

    # Clean and split insights
    insights = [
        line.lstrip("-* ").strip()
        for line in insights_text.splitlines()
        if line.strip()
        and not any(x in line.lower() for x in ["insight", "below", "here"])
    ]
    return insights


def get_market_technical_snapshot():
    """Main function to get technical snapshot and insights."""
    snapshot = fetch_technical_snapshot()
    if not snapshot:
        raise RuntimeError("No stock data available.")

    insights = generate_insights(snapshot)
    result = {
        "date": get_previous_trading_day(),
        "snapshot": snapshot,
        "insights": insights,
    }
    return result
