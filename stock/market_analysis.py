from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import json
from typing import Dict, Any
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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
}


class MarketAnalysisGenerator:
    """
    Generates market analysis and summary using LangChain with Google's Gemini model.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the MarketAnalysisGenerator.

        Args:
            api_key: Google API key for Gemini. If None, will look for GEMINI_API_KEY environment variable.
        """
        # Use provided API key or get from environment variables
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable or pass it directly."
            )

        # Validate API key - it should be a non-empty string
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise ValueError("Gemini API key must be a non-empty string")

        try:
            # Initialize Gemini model with explicit error handling
            # Updated to use gemini-1.5-flash model
            self.llm = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,  # Use the correct parameter name
                temperature=0.2,
                top_p=0.9,
                max_output_tokens=2048,
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini model: {str(e)}")

    def generate_market_analysis(self, market_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive market analysis based on all available data.

        Args:
            market_data: Full market data dictionary with all sections

        Returns:
            str: Detailed market analysis
        """
        # Create prompt template for market analysis
        analysis_template = PromptTemplate(
            input_variables=["market_data"],
            template="""
        You are an expert financial analyst specializing in Indian stock markets.
        Analyze the following market data and present your insights in a structured and concise manner.

        Focus your response on the most critical and impactful observations from the following aspects:
        - Overall market sentiment and direction
        - Sector-specific movements and standout sectors
        - Key technical indicators and their interpretations
        - Institutional investment activity (FII/DII)
        - Notable news events and their market implications
        - Global market cues and potential catalysts

        Guidelines:
        - Provide exactly 6-7 key insights in bullet points.
        - Each point should be one sentence maximum.
        - Use a professional tone with no hedging or generic language.
        - Avoid repetition and maintain high information density.
        - Focus on actionable insights and clear market implications.

        Market Data:
        {market_data}

        Write your analysis as 6-7 powerful bullet points:
        """,
        )

        # Create LLMChain for market analysis
        analysis_chain = LLMChain(llm=self.llm, prompt=analysis_template)

        # Convert market data to string format for the prompt
        market_data_str = json.dumps(market_data, indent=2)

        try:
            # Use invoke() method instead of deprecated run()
            result = analysis_chain.invoke({"market_data": market_data_str})
            analysis = (
                result["text"]
                if isinstance(result, dict) and "text" in result
                else result
            )
            return analysis.strip()
        except Exception as e:
            raise ValueError(f"Failed to generate market analysis: {str(e)}")

    def generate_market_summary(
        self, market_data: Dict[str, Any], market_analysis: str
    ) -> str:
        """
        Generate a concise summary of the entire market report.

        Args:
            market_data: Full market data dictionary with all sections
            market_analysis: The previously generated market analysis

        Returns:
            str: Concise market summary
        """
        # Create prompt template for market summary
        summary_template = PromptTemplate(
            input_variables=["market_data", "market_analysis"],
            template="""
        You are an expert financial analyst specializing in Indian stock markets.
        Create a concise executive summary of the following market data and analysis.

        Focus your summary on the most impactful insights from the report, including:
        - Key market takeaways and directional sentiment
        - Sector highlights and underperformers
        - Notable technical and institutional indicators (FII/DII)
        - Significant macro or news-related influences
        - Summary metrics with implications
        - A short forward-looking outlook

        Guidelines:
        - Present exactly 6-7 high-impact bullet points
        - Each point must be one sentence maximum
        - Use a confident, professional tone with actionable language
        - Avoid narrative fluff and general statements
        - Focus on clear market implications and actionable insights

        Market Data:
        {market_data}

        Market Analysis:
        {market_analysis}

        Write your executive summary as 6-7 strong bullet points:
        """,
        )

        # Create LLMChain for market summary
        summary_chain = LLMChain(llm=self.llm, prompt=summary_template)

        # Convert market data to string format for the prompt
        market_data_str = json.dumps(market_data, indent=2)

        try:
            # Use invoke() method instead of deprecated run()
            result = summary_chain.invoke(
                {"market_data": market_data_str, "market_analysis": market_analysis}
            )
            summary = (
                result["text"]
                if isinstance(result, dict) and "text" in result
                else result
            )
            return summary.strip()
        except Exception as e:
            raise ValueError(f"Failed to generate market summary: {str(e)}")
