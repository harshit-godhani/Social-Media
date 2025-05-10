from fpdf import FPDF
import os
from datetime import datetime
import re
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("market_api.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MarketReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()

    def header(self):
        # Set up header with title and date
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "Daily Market Insights Report", 0, 1, "C")
        self.set_font("helvetica", "", 10)
        self.cell(
            0,
            5,
            f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            0,
            1,
            "C",
        )
        self.ln(5)

    def footer(self):
        # Set up footer with page number
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def create_section_title(self, title):
        self.set_font("helvetica", "B", 14)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, title, 0, 1, "L", fill=True)
        self.ln(2)

    def add_insights(self, insights_text):
        """Process and display insights with bullet points and proper formatting"""
        self.set_font("helvetica", "", 10)

        # Extract each bullet point with its bold text
        bullet_pattern = r"\*\s+\*\*(.*?)\*\*(.*?)(?=\n\*|\Z)"
        bullet_points = re.findall(bullet_pattern, insights_text, re.DOTALL)

        if not bullet_points:
            # Fallback if the regex doesn't match
            self.multi_cell(0, 5, insights_text.strip())
            return

        for point in bullet_points:
            bold_text = point[0].strip()
            remaining_text = point[1].strip()

            # Check for positive/negative indicators to determine color
            color = (0, 0, 0)  # Default black
            if any(
                word in bold_text.lower()
                for word in [
                    "bullish",
                    "strength",
                    "positive",
                    "opportunities",
                    "strongest",
                ]
            ):
                color = (0, 128, 0)  # Green for positive insights
            elif any(
                word in bold_text.lower()
                for word in ["bearish", "cautious", "negative", "selling", "risk"]
            ):
                color = (220, 0, 0)  # Red for negative insights

            # Add bullet point - using standard "-" instead of unicode bullet
            self.set_font("helvetica", "", 10)
            self.cell(5, 5, "-", 0, 0, "L")

            # Add the bold part with appropriate color
            self.set_text_color(*color)
            self.set_font("helvetica", "B", 10)
            self.write(5, f"{bold_text}: ")

            # Add the remaining text in regular font and black color
            self.set_text_color(0, 0, 0)
            self.set_font("helvetica", "", 10)

            # Write the remaining text
            self.write(5, f"{remaining_text}")
            self.ln(8)  # Add space between bullet points

        # Reset text color
        self.set_text_color(0, 0, 0)

    def create_sector_table(self, sectors_data):
        self.set_font("helvetica", "B", 9)

        # Table header - removed source column
        col_widths = [70, 25, 25, 25, 30]
        headers = ["Sector Name", "Companies", "Advances", "Declines", "Change %"]

        # Set header background
        self.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, "C", fill=True)
        self.ln()

        # Table data
        self.set_font("helvetica", "", 8)
        for sector in sectors_data:
            # Replace "Realty" with "Real Estate"
            sector_name = (
                "Real Estate"
                if sector["sector_name"] == "Realty"
                else sector["sector_name"]
            )

            # Set text color based on change percentage
            if sector["change_percentage"] > 0:
                self.set_text_color(0, 128, 0)  # Green for positive
            else:
                self.set_text_color(220, 0, 0)  # Red for negative

            self.cell(col_widths[0], 7, sector_name, 1, 0, "L")
            self.cell(col_widths[1], 7, str(sector["num_companies"]), 1, 0, "C")
            self.cell(col_widths[2], 7, str(sector["advances"]), 1, 0, "C")
            self.cell(col_widths[3], 7, str(sector["declines"]), 1, 0, "C")

            # Format change percentage with + sign for positive values
            change_str = (
                f"+{sector['change_percentage']:.2f}%"
                if sector["change_percentage"] > 0
                else f"{sector['change_percentage']:.2f}%"
            )
            self.cell(col_widths[4], 7, change_str, 1, 0, "C")
            self.ln()

        # Reset text color
        self.set_text_color(0, 0, 0)

    def create_institutional_table(self, institutional_data):
        self.set_font("helvetica", "B", 9)

        # Table header - no source column
        col_widths = [50, 45, 45, 40]
        headers = [
            "Institution",
            "Buy (INR Cr)",
            "Sell (INR Cr)",
            "Net (INR Cr)",
        ]  # Unicode INR works with fpdf2

        # Set header background
        self.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, "C", fill=True)
        self.ln()

        # Table data
        self.set_font("helvetica", "", 8)

        # FII data
        self.cell(col_widths[0], 7, "FII", 1, 0, "L")
        self.cell(
            col_widths[1], 7, f"{institutional_data['fii']['buy_value']:.2f}", 1, 0, "R"
        )
        self.cell(
            col_widths[2],
            7,
            f"{institutional_data['fii']['sell_value']:.2f}",
            1,
            0,
            "R",
        )

        # Set color based on net value
        if institutional_data["fii"]["net_value"] > 0:
            self.set_text_color(0, 128, 0)  # Green for positive
            net_val = f"+{institutional_data['fii']['net_value']:.2f}"
        else:
            self.set_text_color(220, 0, 0)  # Red for negative
            net_val = f"{institutional_data['fii']['net_value']:.2f}"

        self.cell(col_widths[3], 7, net_val, 1, 0, "R")
        self.ln()

        # Reset text color
        self.set_text_color(0, 0, 0)

        # DII data
        self.cell(col_widths[0], 7, "DII", 1, 0, "L")
        self.cell(
            col_widths[1], 7, f"{institutional_data['dii']['buy_value']:.2f}", 1, 0, "R"
        )
        self.cell(
            col_widths[2],
            7,
            f"{institutional_data['dii']['sell_value']:.2f}",
            1,
            0,
            "R",
        )

        # Set color based on net value
        if institutional_data["dii"]["net_value"] > 0:
            self.set_text_color(0, 128, 0)  # Green for positive
            net_val = f"+{institutional_data['dii']['net_value']:.2f}"
        else:
            self.set_text_color(220, 0, 0)  # Red for negative
            net_val = f"{institutional_data['dii']['net_value']:.2f}"

        self.cell(col_widths[3], 7, net_val, 1, 0, "R")
        self.ln()

        # Reset text color
        self.set_text_color(0, 0, 0)


# Function with the name that matches what your code is calling
def generate_pdf_report_individual(market_data):
    """
    Generate a PDF report from market data and return the path

    Args:
        market_data (dict): Market data with sector and institutional information

    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "temp_pdfs"
        )
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"market_report_{timestamp}.pdf")

        # Create PDF object
        pdf = MarketReportPDF()

        # Section 1: Sector Movement
        pdf.create_section_title("Key Insights of Sector Movement")

        # Check if insight exists in the data
        if "insight" in market_data["sector_movement"]:
            pdf.add_insights(market_data["sector_movement"]["insight"])
        else:
            pdf.multi_cell(0, 5, "No sector insights available.")
        pdf.ln(5)

        pdf.create_section_title("Sector-wise Movement")
        pdf.create_sector_table(market_data["sector_movement"]["data"])
        pdf.ln(10)

        # Section 2: Institutional Activity
        pdf.create_section_title("Key Insights of FII & DII Activity")

        # Check if insight exists in the data
        if "insight" in market_data["institutional_activity"]:
            pdf.add_insights(market_data["institutional_activity"]["insight"])
        else:
            pdf.multi_cell(0, 5, "No institutional activity insights available.")
        pdf.ln(5)

        pdf.create_section_title("FII & DII Data")
        pdf.create_institutional_table(market_data["institutional_activity"]["data"])

        # Save PDF
        pdf.output(output_path)
        logger.info(f"PDF report generated at: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise


# Also provide the two-argument version for compatibility
def generate_pdf_report(market_data, output_path=None):
    """
    Generate a PDF report from market data and save it to the specified path

    Args:
        market_data (dict): Market data with sector and institutional information
        output_path (str, optional): Path to save the PDF. If None, a temp file is created.

    Returns:
        str: Path to the generated PDF file
    """
    if output_path is None:
        return generate_pdf_report_individual(market_data)

    try:
        # Create PDF object
        pdf = MarketReportPDF()

        # Section 1: Sector Movement
        pdf.create_section_title("Key Insights of Sector Movement")

        # Check if insight exists in the data
        if "insight" in market_data["sector_movement"]:
            pdf.add_insights(market_data["sector_movement"]["insight"])
        else:
            pdf.multi_cell(0, 5, "No sector insights available.")
        pdf.ln(5)

        pdf.create_section_title("Sector-wise Movement")
        pdf.create_sector_table(market_data["sector_movement"]["data"])
        pdf.ln(10)

        # Section 2: Institutional Activity
        pdf.create_section_title("Key Insights of FII & DII Activity")

        # Check if insight exists in the data
        if "insight" in market_data["institutional_activity"]:
            pdf.add_insights(market_data["institutional_activity"]["insight"])
        else:
            pdf.multi_cell(0, 5, "No institutional activity insights available.")
        pdf.ln(5)

        pdf.create_section_title("FII & DII Data")
        pdf.create_institutional_table(market_data["institutional_activity"]["data"])

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save PDF
        pdf.output(output_path)
        return output_path

    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise


def cleanup_old_files(directory, max_age_seconds):
    """Delete files older than max_age_seconds from the directory"""
    try:
        now = datetime.now()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = now - datetime.fromtimestamp(os.path.getctime(file_path))
                if file_age.total_seconds() > max_age_seconds:
                    os.remove(file_path)
                    logger.info(f"Deleted old file: {filename}")
    except Exception as e:
        logger.error(f"Error cleaning up old files: {str(e)}")
