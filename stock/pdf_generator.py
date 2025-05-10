import os
import json
from datetime import datetime
from fpdf import FPDF
import uuid
import re


class IndianStockMarketPDFGenerator:
    """
    Generates a PDF report for the Indian stock market from JSON data.
    """

    def __init__(self, output_dir="reports"):
        """Initialize the PDF generator."""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pdf(self, data):
        """
        Generate a PDF report from the provided JSON data.
        Args:
            data (dict): A dictionary containing the stock market data
        Returns:
            str: The file path of the generated PDF
        """
        try:
            filename = f"Stock_Market_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
            file_path = os.path.join(self.output_dir, filename)

            data = self.sanitize_unicode_chars(data)

            # Initialize PDF with proper error handling
            pdf = StockMarketPDF()
            if not hasattr(pdf, "blue_color"):
                raise AttributeError("PDF object missing required color attributes")

            pdf.add_title_page(data)
            pdf.add_market_analysis(data)  # Market Analysis with bullet points
            pdf.add_market_overview(data)  # Market Overview with insight first
            pdf.add_sector_movements(data)  # Sector performance with insight first
            pdf.add_top_performers(data)  # Top performers with insight first
            pdf.add_institutional_activity(
                data
            )  # Institutional activity with insight first
            pdf.add_news_highlights(data)  # News highlights in bullet points
            pdf.add_technical_snapshot(data)  # Technical snapshot with insight first
            pdf.add_financial_indicators(
                data
            )  # Macro and global cues with insight first
            pdf.add_summary(data)  # Summary in bullet points

            pdf.output(file_path)
            return file_path
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")

    def sanitize_unicode_chars(self, data):
        """
        Recursively replaces unsupported curly quotes and symbols in the data dictionary with supported ASCII characters.
        """
        replacements = {
            "’": "'",
            "‘": "'",
            "“": '"',
            "”": '"',
            "–": "-",  # en dash
            "—": "-",  # em dash
            "…": "...",  # ellipsis
        }

        def replace_in_string(s):
            for bad, good in replacements.items():
                s = s.replace(bad, good)
            return s

        if isinstance(data, dict):
            return {k: self.sanitize_unicode_chars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_unicode_chars(item) for item in data]
        elif isinstance(data, str):
            return replace_in_string(data)
        else:
            return data


class StockMarketPDF(FPDF):
    """Custom PDF class for generating Indian Stock Market reports."""

    def __init__(self):
        """Initialize the PDF with A4 format"""
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

        # Define colors
        self.blue_color = (0, 83 / 255, 155 / 255)  # Dark blue for titles
        self.green_color = (0, 128 / 255, 0)  # Green for positive values
        self.red_color = (255 / 255, 0, 0)  # Red for negative values
        self.gray_color = (
            240 / 255,
            240 / 255,
            240 / 255,
        )  # Light gray for backgrounds
        self.dark_gray = (
            100 / 255,
            100 / 255,
            100 / 255,
        )  # Dark gray for secondary text

        # Set page margins and orientation
        self.set_margins(left=10, top=10, right=10)
        self.add_page()

        # Set default font
        self.set_font("Arial", size=10)

    def header(self):
        """Add header to each page"""
        # Set font and color for header
        self.set_font("Arial", "B", 16)
        self.set_text_color(*self.blue_color)

        # Add title
        self.cell(0, 10, "Indian Stock Market Report", 0, 1, "C")

        # Add date
        self.set_font("Arial", "I", 10)
        self.set_text_color(*self.dark_gray)
        self.cell(0, 5, datetime.now().strftime("%d %B %Y"), 0, 1, "C")

        # Reset font and color
        self.set_font("Arial", "", 10)
        self.set_text_color(0, 0, 0)
        self.ln(10)

    def footer(self):
        """Add a footer to each page"""
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(*self.dark_gray)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def section_title(self, title, top_margin=10, bottom_margin=5):
        """Add a section title with consistent formatting"""
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.blue_color)
        self.ln(top_margin)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(bottom_margin)
        self.set_font("Arial", "", 10)
        self.set_text_color(0, 0, 0)

    def add_title_page(self, data):
        """Create a title page for the report"""
        self.set_font("Arial", "B", 24)
        self.set_text_color(*self.blue_color)
        self.cell(0, 20, "Indian Stock Market Report", 0, 1, "C")

        self.set_font("Arial", "", 14)
        self.set_text_color(*self.dark_gray)
        date_str = data.get("market_snapshot", {}).get(
            "date", datetime.now().strftime("%B %d, %Y")
        )
        self.cell(0, 10, f"Date: {date_str}", 0, 1, "C")

        timestamp = data.get("_meta", {}).get("timestamp", datetime.now().isoformat())
        try:
            dt_obj = datetime.fromisoformat(timestamp)
            formatted_time = dt_obj.strftime("%I:%M %p")
            self.cell(0, 10, f"Generated at: {formatted_time}", 0, 1, "C")
        except:
            self.cell(
                0, 10, f"Generated at: {datetime.now().strftime('%I:%M %p')}", 0, 1, "C"
            )
        self.ln(20)

    def create_table_header(self, headers, col_widths):
        """Create a consistent table header with styling"""
        self.set_font("Arial", "B", 10)
        self.set_fill_color(*self.gray_color)
        self.set_text_color(*self.dark_gray)

        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, "C", 1)
        self.ln()

        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "", 9)

    def add_market_analysis(self, data):
        """Add market analysis section with bullet points"""
        if self.get_y() > 250:
            self.add_page()
        self.section_title("1. Market Analysis")

        analysis = data.get("market_analysis", {}).get("analysis", "")
        if not analysis:
            self.cell(0, 8, "Market analysis data not available", 0, 1)
            return

        bullet_points = [line.strip() for line in analysis.split("\n") if line.strip()]
        self.set_font("Arial", "", 10)

        for point in bullet_points:
            if point.startswith("*") or point.startswith("-"):
                self.set_x(self.get_x() + 5)
                self.cell(5, 5, "-", 0, 0)
                point = point.replace("₹", "INR")

                # Color code based on sentiment
                if any(
                    word in point.lower()
                    for word in ["positive", "up", "gain", "strong", "bullish"]
                ):
                    self.set_text_color(*self.green_color)
                elif any(
                    word in point.lower()
                    for word in ["negative", "down", "loss", "weak", "bearish"]
                ):
                    self.set_text_color(*self.red_color)

                self.multi_cell(0, 5, point[1:].strip(), 0)
                self.set_text_color(0, 0, 0)
                self.ln(2)
            else:
                point = point.replace("₹", "INR")
                self.multi_cell(0, 5, point)
                self.ln(2)
        self.ln(5)

    def add_market_overview(self, data):
        """Add market overview section with insights first"""
        # Only add new page if we're near the bottom
        if self.get_y() > 250:
            self.add_page()
        self.section_title("2. Market Overview")

        # Add insights first
        insights = data.get("market_overview", {}).get("insights", "")
        if insights:
            self.set_font("Arial", "B", 10)
            self.cell(0, 8, "Market Insights:", 0, 1)
            self.set_font("Arial", "", 9)
            # Split insights into bullet points
            insight_points = [
                line.strip() for line in insights.split("\n") if line.strip()
            ]
            for point in insight_points:
                self.set_x(self.get_x() + 5)
                self.cell(5, 5, "-", 0, 0)
                # Color code based on sentiment
                if any(
                    word in point.lower()
                    for word in ["positive", "up", "gain", "strong", "bullish"]
                ):
                    self.set_text_color(*self.green_color)
                elif any(
                    word in point.lower()
                    for word in ["negative", "down", "loss", "weak", "bearish"]
                ):
                    self.set_text_color(*self.red_color)
                self.multi_cell(0, 5, point.replace("₹", "INR"))
                self.set_text_color(0, 0, 0)
                self.ln(2)
            self.ln(5)

        # Add market data table
        market_data = data.get("market_overview", {}).get("market_data", {})
        if not market_data or "_meta" not in market_data:
            self.cell(0, 8, "Market overview data not available", 0, 1)
            return

        self.set_font("Arial", "B", 10)
        self.cell(0, 8, "Index Performance:", 0, 1)
        self.set_font("Arial", "B", 9)

        col_widths = [45, 25, 25, 25, 25, 30]
        headers = ["Index", "Open", "High", "Low", "Close", "% Change"]

        # Draw header row with light gray background
        self.set_fill_color(240, 240, 240)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, "C", 1)
        self.ln()

        self.set_font("Arial", "", 8)
        indices = {
            "^NSEI": "Nifty 50",
            "^BSESN": "Sensex",
            "^CRSLDX": "Nifty 500",
            "^NSEBANK": "Bank Nifty",
            "^CNXIT": "Nifty IT",
            "^NSEMDCP50": "Nifty Midcap",
        }

        for index_code, index_name in indices.items():
            if index_code in market_data and not market_data[index_code].get(
                "Error", ""
            ):
                index_info = market_data[index_code]
                self.cell(col_widths[0], 8, index_name, 1, 0)
                self.cell(col_widths[1], 8, str(index_info.get("Open", "N/A")), 1, 0)
                self.cell(col_widths[2], 8, str(index_info.get("High", "N/A")), 1, 0)
                self.cell(col_widths[3], 8, str(index_info.get("Low", "N/A")), 1, 0)
                self.cell(col_widths[4], 8, str(index_info.get("Close", "N/A")), 1, 0)

                change_pct = index_info.get("Change%", 0)
                if isinstance(change_pct, (int, float)):
                    self.set_text_color(
                        *self.green_color if change_pct >= 0 else self.red_color
                    )
                    self.cell(col_widths[5], 8, f"{change_pct:.2f}%", 1, 0, "C")
                else:
                    self.cell(col_widths[5], 8, str(change_pct), 1, 0, "C")

                self.set_text_color(0, 0, 0)
                self.ln()

    def add_sector_movements(self, data):
        """Add sector movements section with color-coded tables"""
        self.set_font("Arial", "B", 16)
        self.set_text_color(*self.blue_color)
        self.cell(0, 10, "Sector Movements", ln=True, align="C")
        self.ln(5)

        # Add sector performance table with color coding
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Sector Performance", ln=True)
        self.ln(2)

        # Table header
        self.set_fill_color(*self.gray_color)
        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "B", 10)
        self.cell(60, 8, "Sector", 1, 0, "C", 1)
        self.cell(30, 8, "Change (%)", 1, 0, "C", 1)
        self.cell(25, 8, "Advances", 1, 0, "C", 1)
        self.cell(25, 8, "Declines", 1, 0, "C", 1)
        self.ln()

        # Table rows with color coding
        self.set_font("Arial", "", 10)
        sectors = data.get("sector_and_fii", {}).get("sector_movements", [])
        for sector in sectors:
            self.cell(60, 8, sector["sector_name"], 1)
            change = float(sector["change_percentage"])
            if change > 0:
                self.set_text_color(*self.green_color)
            elif change < 0:
                self.set_text_color(*self.red_color)
            self.cell(30, 8, f"{change:.2f}%", 1)
            self.set_text_color(0, 0, 0)
            self.cell(25, 8, str(sector["advances"]), 1)
            self.cell(25, 8, str(sector["declines"]), 1)
            self.ln()

        self.ln(5)

        # Add sector insights
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Sector Insights", ln=True)
        self.ln(2)

        insights = data.get("sector_and_fii", {}).get("sector_insights", "")
        if insights:
            self.set_font("Arial", "", 10)
            self.multi_cell(0, 6, insights)
        else:
            self.set_font("Arial", "I", 10)
            self.cell(0, 6, "No sector insights available", ln=True)

        self.ln(10)

    def add_institutional_activity(self, data):
        """Add institutional activity section with color-coded tables"""
        self.set_font("Arial", "B", 16)
        self.set_text_color(*self.blue_color)
        self.cell(0, 10, "Institutional Activity", ln=True, align="C")
        self.ln(5)

        # Add FII/DII table with color coding
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "FII/DII Activity", ln=True)
        self.ln(2)

        # Table header
        self.set_fill_color(*self.gray_color)
        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "B", 10)
        self.cell(40, 8, "Category", 1, 0, "C", 1)
        self.cell(40, 8, "Buy (Cr)", 1, 0, "C", 1)
        self.cell(40, 8, "Sell (Cr)", 1, 0, "C", 1)
        self.cell(40, 8, "Net (Cr)", 1, 0, "C", 1)
        self.ln()

        # Table rows with color coding
        self.set_font("Arial", "", 10)
        institutional_data = data.get("sector_and_fii", {}).get(
            "institutional_activity", {}
        )

        # FII row
        fii = institutional_data.get("fii", {})
        self.cell(40, 8, "FII", 1)
        self.cell(40, 8, f"{fii.get('buy_value', 0):.2f}", 1)
        self.cell(40, 8, f"{fii.get('sell_value', 0):.2f}", 1)
        net = float(fii.get("net_value", 0))
        if net > 0:
            self.set_text_color(*self.green_color)
        elif net < 0:
            self.set_text_color(*self.red_color)
        self.cell(40, 8, f"{net:.2f}", 1)
        self.set_text_color(0, 0, 0)
        self.ln()

        # DII row
        dii = institutional_data.get("dii", {})
        self.cell(40, 8, "DII", 1)
        self.cell(40, 8, f"{dii.get('buy_value', 0):.2f}", 1)
        self.cell(40, 8, f"{dii.get('sell_value', 0):.2f}", 1)
        net = float(dii.get("net_value", 0))
        if net > 0:
            self.set_text_color(*self.green_color)
        elif net < 0:
            self.set_text_color(*self.red_color)
        self.cell(40, 8, f"{net:.2f}", 1)
        self.set_text_color(0, 0, 0)
        self.ln()

        self.ln(5)

        # Add institutional insights
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Institutional Insights", ln=True)
        self.ln(2)

        insights = data.get("sector_and_fii", {}).get("institutional_insights", "")
        if insights:
            self.set_font("Arial", "", 10)
            self.multi_cell(0, 6, insights)
        else:
            self.set_font("Arial", "I", 10)
            self.cell(0, 6, "No institutional insights available", ln=True)

        self.ln(10)

    def add_top_performers(self, data):
        """Add top performers section"""
        # Only add new page if we're near the bottom
        if self.get_y() > 250:
            self.add_page()
        self.section_title("5. Top Gainers & Losers")

        # Add insights first
        self.set_font("Arial", "B", 11)
        self.set_text_color(*self.blue_color)
        self.cell(0, 8, "Market Performers Insights:", 0, 1)
        self.set_font("Arial", "", 10)
        self.set_text_color(0, 0, 0)

        # Calculate available width
        page_width = self.w - self.l_margin - self.r_margin

        insight = data.get("top_performers", {}).get("insight", "")
        if insight:
            lines = insight.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    self.set_x(self.l_margin + 5)
                    self.cell(5, 5, "-", 0, 0)
                    line = line.replace("₹", "INR")
                    # Use most of available width for multi_cell
                    self.multi_cell(page_width - 10, 5, line)
            self.ln(3)
        else:
            self.cell(0, 8, "No market performers insights available", 0, 1)

        # Add top gainers table
        self.set_font("Arial", "B", 11)
        self.set_text_color(*self.blue_color)
        self.cell(0, 8, "Top Gainers:", 0, 1)

        # Define column widths based on available page width
        col_widths = [page_width - 80, 45, 35]  # Company name gets remaining space
        headers = ["Company", "Price", "%"]

        # Create table header with borders
        self.set_font("Arial", "B", 10)
        self.set_text_color(0, 0, 0)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, 1, 0, "C")
        self.ln()

        # Add table content
        self.set_font("Arial", "", 10)
        top_gainers = data.get("top_performers", {}).get("top_gainers", [])
        for stock in top_gainers[:10]:
            # Truncate company name if too long
            company_name = stock["company_name"]
            if len(company_name) > 40:
                company_name = company_name[:37] + "..."

            self.cell(col_widths[0], 7, company_name, 1, 0)
            self.cell(col_widths[1], 7, f"{stock['current_price']:.1f}", 1, 0, "R")
            self.set_text_color(*self.green_color)
            self.cell(
                col_widths[2], 7, f"+{stock['percentage_change']:.1f}%", 1, 0, "R"
            )
            self.set_text_color(0, 0, 0)
            self.ln()

        self.ln(3)

        # Add top losers table
        self.set_font("Arial", "B", 11)
        self.set_text_color(*self.blue_color)
        self.cell(0, 8, "Top Losers:", 0, 1)

        # Create table header with borders
        self.set_font("Arial", "B", 10)
        self.set_text_color(0, 0, 0)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, 1, 0, "C")
        self.ln()

        # Add table content
        self.set_font("Arial", "", 10)
        top_losers = data.get("top_performers", {}).get("top_losers", [])
        for stock in top_losers[:10]:
            # Truncate company name if too long
            company_name = stock["company_name"]
            if len(company_name) > 40:
                company_name = company_name[:37] + "..."

            self.cell(col_widths[0], 7, company_name, 1, 0)
            self.cell(col_widths[1], 7, f"{stock['current_price']:.1f}", 1, 0, "R")
            self.set_text_color(*self.red_color)
            self.cell(col_widths[2], 7, f"{stock['percentage_change']:.1f}%", 1, 0, "R")
            self.set_text_color(0, 0, 0)
            self.ln()

        self.ln(3)  # Reduced spacing after section

    def add_technical_snapshot(self, data):
        """Add technical snapshot section with insights first"""
        self.add_page()
        self.section_title("7. Technical Snapshot")

        # Add insights first
        insights = data.get("market_snapshot", {}).get("insights", [])
        if insights:
            self.set_font("Arial", "B", 11)
            self.cell(0, 10, "Technical Insights:", 0, 1)
            self.set_font("Arial", "", 10)
            for insight in insights:
                self.set_x(self.get_x() + 5)
                self.cell(5, 5, "-", 0, 0)  # Using hyphen for bullets
                # Replace ₹ with INR
                insight = insight.replace("₹", "INR")
                self.multi_cell(0, 5, insight)
                self.ln(2)
            self.ln(10)

        # Add technical data table
        snapshot = data.get("market_snapshot", {}).get("snapshot", {})
        if not snapshot:
            self.cell(0, 10, "Technical snapshot data not available", 0, 1)
            return

        self.set_font("Arial", "B", 10)
        col_widths = [40, 30, 30, 30, 60]
        headers = ["Index", "Close", "Support", "RSI", "MACD"]

        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, "C")
        self.ln()

        self.set_font("Arial", "", 9)
        for index_name, index_data in snapshot.items():
            self.cell(col_widths[0], 10, index_name, 1, 0)
            self.cell(
                col_widths[1], 10, f"{index_data.get('close', 0):,.2f}", 1, 0, "R"
            )
            self.cell(
                col_widths[2], 10, f"{index_data.get('support', 0):,.2f}", 1, 0, "R"
            )

            # RSI
            rsi = index_data.get("rsi", 0)
            if rsi > 70:
                self.set_text_color(*self.red_color)  # Overbought
            elif rsi < 30:
                self.set_text_color(*self.red_color)  # Oversold
            else:
                self.set_text_color(0, 0, 0)  # Normal
            self.cell(col_widths[3], 10, f"{rsi:,.2f}", 1, 0, "R")

            # MACD
            macd = index_data.get("macd", {})
            macd_line = macd.get("line", 0)
            macd_signal = macd.get("signal", 0)

            if macd_line > macd_signal:
                self.set_text_color(*self.green_color)  # Bullish
                macd_text = f"{macd_line:,.2f} > {macd_signal:,.2f}"
            else:
                self.set_text_color(*self.red_color)  # Bearish
                macd_text = f"{macd_line:,.2f} < {macd_signal:,.2f}"

            self.cell(col_widths[4], 10, macd_text, 1, 0, "C")
            self.set_text_color(0, 0, 0)  # Reset text color
            self.ln()

    def add_news_highlights(self, data):
        """Add news highlights section to the PDF"""
        self.section_title("News Highlights")

        # Get news data
        news_data = data.get("news_highlights", {})
        if not news_data:
            self.set_font("Arial", "I", 10)
            self.cell(0, 6, "No news highlights available", ln=True)
            return

        # Add Impact News section
        self.set_font("Arial", "B", 12)
        self.set_text_color(*self.blue_color)
        self.cell(0, 10, "Impact News", ln=True)
        self.ln(2)

        impact_news = news_data.get("impact", [])
        if impact_news:
            self.set_font("Arial", "", 10)
            self.set_text_color(0, 0, 0)
            for news in impact_news:
                self.multi_cell(0, 6, f"• {news}")
        else:
            self.set_font("Arial", "I", 10)
            self.cell(0, 6, "No impact news available", ln=True)

        self.ln(5)

        # Add India News section
        self.set_font("Arial", "B", 12)
        self.set_text_color(*self.blue_color)
        self.cell(0, 10, "India News", ln=True)
        self.ln(2)

        india_news = news_data.get("india", [])
        if india_news:
            self.set_font("Arial", "", 10)
            self.set_text_color(0, 0, 0)
            for news in india_news:
                self.multi_cell(0, 6, f"• {news}")
        else:
            self.set_font("Arial", "I", 10)
            self.cell(0, 6, "No India news available", ln=True)

        self.ln(5)

        # Add Global News section
        self.set_font("Arial", "B", 12)
        self.set_text_color(*self.blue_color)
        self.cell(0, 10, "Global News", ln=True)
        self.ln(2)

        global_news = news_data.get("global", [])
        if global_news:
            self.set_font("Arial", "", 10)
            self.set_text_color(0, 0, 0)
            for news in global_news:
                self.multi_cell(0, 6, f"• {news}")
        else:
            self.set_font("Arial", "I", 10)
            self.cell(0, 6, "No global news available", ln=True)

        self.ln(10)

    def add_financial_indicators(self, data):
        """Add financial indicators section with insights first"""
        self.add_page()
        self.section_title("8. Macro and Global Cues")

        # Add insights first
        self.set_font("Arial", "B", 11)
        self.cell(0, 10, "Global Market Insights:", 0, 1)
        self.set_font("Arial", "", 10)

        # Create insights based on the data
        indicators = data.get("financial_indicators", {}).get("indicators", {})
        insights = []

        if indicators.get("Dow Jones", {}).get("remarks") == "Up":
            insights.append("Dow Jones showing positive momentum")
        if indicators.get("Nasdaq", {}).get("remarks") == "Down":
            insights.append("Nasdaq experiencing some pressure")
        if indicators.get("Crude Oil (Brent)", {}).get("remarks") == "Down":
            insights.append("Crude oil prices declining")
        if indicators.get("USD/INR", {}).get("remarks") == "INR weakened":
            insights.append("Indian Rupee showing weakness against USD")
        if indicators.get("India 10Y Yield", {}).get("remarks") == "Up":
            insights.append(
                "Rising bond yields indicating potential inflationary pressure"
            )

        for insight in insights:
            self.set_x(self.get_x() + 5)
            self.cell(5, 5, "-", 0, 0)  # Using hyphen for bullets
            # Replace ₹ with INR
            insight = insight.replace("₹", "INR")
            self.multi_cell(0, 5, insight)
            self.ln(2)
        self.ln(10)

        # Add financial indicators table
        if not indicators:
            self.cell(0, 10, "Financial indicators data not available", 0, 1)
            return

        self.set_font("Arial", "B", 10)
        col_widths = [60, 40, 30, 60]
        headers = ["Indicator", "Value", "Change", "Remarks"]

        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, "C")
        self.ln()

        self.set_font("Arial", "", 10)
        for indicator, values in indicators.items():
            self.cell(col_widths[0], 10, indicator, 1, 0)
            self.cell(col_widths[1], 10, values.get("value", "N/A"), 1, 0, "C")

            # Change percentage with color
            pct_change = values.get("percent_change", "N/A")
            if pct_change != "N/A":
                try:
                    pct_float = float(pct_change.replace("%", ""))
                    self.set_text_color(
                        *self.green_color if pct_float >= 0 else self.red_color
                    )
                except ValueError:
                    self.set_text_color(0, 0, 0)
            else:
                self.set_text_color(0, 0, 0)

            self.cell(col_widths[2], 10, pct_change, 1, 0, "C")

            # Remarks
            remarks = values.get("remarks", "")
            if "Up" in remarks:
                self.set_text_color(*self.green_color)
            elif "Down" in remarks:
                self.set_text_color(*self.red_color)
            else:
                self.set_text_color(0, 0, 0)

            self.cell(col_widths[3], 10, remarks, 1, 0, "C")
            self.set_text_color(0, 0, 0)  # Reset text color
            self.ln()

    def add_summary(self, data):
        """Add summary section in bullet points"""
        # Only add new page if we're near the bottom
        if self.get_y() > 250:
            self.add_page()
        self.section_title("9. Summary")

        # Get summary content
        summary = data.get("summary", {}).get("content", "")
        if not summary:
            self.cell(0, 8, "Summary data not available", 0, 1)
            return

        # Split the summary into bullet points
        bullet_points = [line.strip() for line in summary.split("\n") if line.strip()]

        self.set_font("Arial", "", 9)
        for point in bullet_points:
            if point.startswith("*") or point.startswith("-"):
                self.set_x(self.get_x() + 5)
                self.cell(5, 5, "-", 0, 0)
                # Replace ₹ with INR
                point = point.replace("₹", "INR")
                # Color code based on sentiment
                if any(
                    word in point.lower()
                    for word in ["positive", "up", "gain", "strong", "bullish"]
                ):
                    self.set_text_color(*self.green_color)
                elif any(
                    word in point.lower()
                    for word in ["negative", "down", "loss", "weak", "bearish"]
                ):
                    self.set_text_color(*self.red_color)
                self.multi_cell(0, 5, point[1:].strip(), 0)
                self.set_text_color(0, 0, 0)
                self.ln(2)
            else:
                # Replace ₹ with INR
                point = point.replace("₹", "INR")
                self.multi_cell(0, 5, point)
                self.ln(2)
        self.ln(5)

        # Add disclaimer
        self.ln(5)
        self.set_font("Arial", "I", 8)
        disclaimer = (
            "Disclaimer: This report is for informational purposes only and should not be considered as financial advice. "
            "The information contained in this report is based on data available at the time of generation and may be "
            "subject to change. Investors are advised to conduct their own research and consult with a financial advisor "
            "before making any investment decisions."
        )
        self.multi_cell(0, 5, disclaimer)

    def add_market_summary(self, data):
        """Add market summary section with color-coded tables"""
        self.set_font("Arial", "B", 16)
        self.set_text_color(*self.blue_color)
        self.cell(0, 10, "Market Summary", ln=True, align="C")
        self.ln(5)

        # Add key indices table with color coding
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Key Indices", ln=True)
        self.ln(2)

        # Table header
        self.set_fill_color(*self.gray_color)
        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "B", 10)
        self.cell(60, 8, "Index", 1, 0, "C", 1)
        self.cell(40, 8, "Value", 1, 0, "C", 1)
        self.cell(40, 8, "Change (%)", 1, 0, "C", 1)
        self.ln()

        # Table rows with color coding
        self.set_font("Arial", "", 10)
        indices = data.get("market_summary", {}).get("indices", [])
        for index in indices:
            self.cell(60, 8, index["name"], 1)
            self.cell(40, 8, str(index["value"]), 1)
            change = float(index["change_percentage"])
            if change > 0:
                self.set_text_color(*self.green_color)
            elif change < 0:
                self.set_text_color(*self.red_color)
            self.cell(40, 8, f"{change:.2f}%", 1)
            self.set_text_color(0, 0, 0)
            self.ln()

        self.ln(5)

        # Add market insights
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Market Insights", ln=True)
        self.ln(2)

        insights = data.get("market_summary", {}).get("insights", "")
        if insights:
            self.set_font("Arial", "", 10)
            self.multi_cell(0, 6, insights)
        else:
            self.set_font("Arial", "I", 10)
            self.cell(0, 6, "No insights available", ln=True)

        self.ln(10)
