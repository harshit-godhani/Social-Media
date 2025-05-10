# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import yfinance as yf
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Financial Data API",
    description="API for fetching real-time market and economic indicators",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class IndicatorData(BaseModel):
    value: str
    percent_change: str
    remarks: Optional[str] = None


class FinancialDashboard(BaseModel):
    last_updated: str
    indicators: Dict[str, IndicatorData]


# Helper functions
def format_value(value, prefix="", suffix=""):
    """Format value with prefix and suffix"""
    if value is None:
        return "N/A"
    return f"{prefix}{value}{suffix}"


def calculate_percent_change(current, previous):
    """Calculate percentage change between two values"""
    if not previous or previous == 0:
        return "N/A"

    change = ((current - previous) / previous) * 100
    return f"{change:.2f}%"


def get_stock_indices():
    """Get major stock indices data"""
    try:
        indices = {"^DJI": "Dow Jones", "^IXIC": "Nasdaq", "^N225": "Nikkei"}

        result = {}
        for symbol, name in indices.items():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="2d")

            if len(data) >= 2:
                current_price = data.iloc[-1]["Close"]
                prev_price = data.iloc[-2]["Close"]
                percent_change = calculate_percent_change(current_price, prev_price)

                result[name] = IndicatorData(
                    value=format_value(round(current_price, 2)),
                    percent_change=percent_change,
                    remarks="Up" if current_price > prev_price else "Down",
                )
            else:
                result[name] = IndicatorData(
                    value="N/A", percent_change="N/A", remarks="Data unavailable"
                )

        return result
    except Exception as e:
        print(f"Error fetching stock indices: {e}")
        return {}


def get_commodities():
    """Get commodity prices"""
    try:
        commodities = {
            "BZ=F": "Crude Oil (Brent)",
        }

        result = {}
        for symbol, name in commodities.items():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="2d")

            if len(data) >= 2:
                current_price = data.iloc[-1]["Close"]
                prev_price = data.iloc[-2]["Close"]
                percent_change = calculate_percent_change(current_price, prev_price)

                result[name] = IndicatorData(
                    value=format_value(round(current_price, 2), "$"),
                    percent_change=percent_change,
                    remarks="Up" if current_price > prev_price else "Down",
                )
            else:
                result[name] = IndicatorData(
                    value="N/A", percent_change="N/A", remarks="Data unavailable"
                )

        return result
    except Exception as e:
        print(f"Error fetching commodities: {e}")
        return {}


def get_gold_price():
    """Get Gold MCX price in INR"""
    try:
        # This is a placeholder. You would need a specific API for MCX Gold in INR
        # For demonstration, we'll use a proxy like gold futures
        ticker = yf.Ticker("GC=F")
        data = ticker.history(period="2d")

        if len(data) >= 2:
            # Convert to INR (rough estimate)
            usd_inr = 75  # Placeholder - should fetch actual rate
            gold_usd = data.iloc[-1]["Close"]
            gold_inr = gold_usd * usd_inr / 10  # Converted to INR/10g

            prev_gold_usd = data.iloc[-2]["Close"]
            prev_gold_inr = prev_gold_usd * usd_inr / 10

            percent_change = calculate_percent_change(gold_inr, prev_gold_inr)

            return {
                "Gold (MCX)": IndicatorData(
                    value=format_value(round(gold_inr, 2), "INR", "/10g"),
                    percent_change=percent_change,
                    remarks="Up" if gold_inr > prev_gold_inr else "Down",
                )
            }
        else:
            return {
                "Gold (MCX)": IndicatorData(
                    value="N/A", percent_change="N/A", remarks="Data unavailable"
                )
            }
    except Exception as e:
        print(f"Error fetching gold price: {e}")
        return {
            "Gold (MCX)": IndicatorData(
                value="N/A", percent_change="N/A", remarks="Error"
            )
        }


def get_currency_rates():
    """Get USD/INR exchange rate"""
    try:
        # Using Yahoo Finance for USD/INR
        ticker = yf.Ticker("INR=X")
        data = ticker.history(period="2d")

        if len(data) >= 2:
            # Note: INR=X gives USD/INR, so we take reciprocal for USD/INR
            current_rate = 1 / data.iloc[-1]["Close"]
            prev_rate = 1 / data.iloc[-2]["Close"]

            percent_change = calculate_percent_change(current_rate, prev_rate)

            return {
                "USD/INR": IndicatorData(
                    value=format_value(round(current_rate, 2)),
                    percent_change=percent_change,
                    remarks=(
                        "INR weakened"
                        if current_rate > prev_rate
                        else "INR strengthened"
                    ),
                )
            }
        else:
            return {
                "USD/INR": IndicatorData(
                    value="N/A", percent_change="N/A", remarks="Data unavailable"
                )
            }
    except Exception as e:
        print(f"Error fetching currency rates: {e}")
        return {
            "USD/INR": IndicatorData(value="N/A", percent_change="N/A", remarks="Error")
        }


def get_bond_yields():
    """Get India 10Y Government Bond Yield"""
    try:
        # For Indian govt bonds, you might need a specialized API
        # This is a placeholder example
        # In production, you would integrate with a bond data provider

        # Sample placeholder for demo purposes:
        current_yield = 7.15  # Placeholder value
        prev_yield = 7.10  # Placeholder value

        percent_change = calculate_percent_change(current_yield, prev_yield)

        return {
            "India 10Y Yield": IndicatorData(
                value=format_value(current_yield, "", "%"),
                percent_change=percent_change,
                remarks="Up" if current_yield > prev_yield else "Down",
            )
        }
    except Exception as e:
        print(f"Error fetching bond yields: {e}")
        return {
            "India 10Y Yield": IndicatorData(
                value="N/A", percent_change="N/A", remarks="Error"
            )
        }


def fetch_all_financial_indicators():
    """
    Fetch all financial indicators from various sources and combine them into a single dictionary

    Returns:
        Dict: Combined dictionary of all financial indicators
    """
    try:
        # Fetch data from different sources
        indices = get_stock_indices()
        commodities = get_commodities()
        gold = get_gold_price()
        currency = get_currency_rates()
        bonds = get_bond_yields()

        # Combine all indicators
        indicators = {**indices, **commodities, **gold, **currency, **bonds}
        return indicators
    except Exception as e:
        print(f"Error in fetch_all_financial_indicators: {e}")
        raise e
