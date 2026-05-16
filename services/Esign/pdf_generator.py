from pathlib import Path
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from core.config import settings
from core.logger import logger


class PDFGenerator:

    def __init__(self):
        # Pathlib-safe creation
        self.output_dir: Path = Path(settings.AGREEMENT_STORAGE_PATH)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_agreement(
        self,
        application_id: int,
        borrower_name: str,
        loan_amount: float,
        interest_rate: float
    ):

        # -------------------------------------------------
        # 🔧 CLEAN + FORMAT VALUES
        # -------------------------------------------------
        borrower_name = borrower_name or "N/A"
        loan_amount = float(loan_amount or 0)
        interest_rate = round(float(interest_rate or 0), 2)

        formatted_amount = f"₹ {loan_amount:,.2f}"
        formatted_rate = f"{interest_rate:.2f}% per year"
        formatted_date = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S UTC")

        # -------------------------------------------------
        # 📁 CREATE DIRECTORY
        # -------------------------------------------------
        loan_dir = self.output_dir / str(application_id)
        loan_dir.mkdir(exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"agreement_v{timestamp}_{application_id}.pdf"
        file_path = loan_dir / file_name

        logger.info(f"[PDF] Generating agreement: {file_path}")

        # -------------------------------------------------
        # 📄 CREATE PDF
        # -------------------------------------------------
        c = canvas.Canvas(str(file_path), pagesize=LETTER)
        width, height = LETTER

        # Title
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width / 2, height - 60, "Loan Agreement Document")

        # Timestamp
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 85, f"Generated On: {formatted_date}")

        # -------------------------------------------------
        # 👤 BORROWER DETAILS
        # -------------------------------------------------
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 120, "Borrower Information")

        c.setFont("Helvetica", 12)
        c.drawString(50, height - 145, f"Borrower Name: {borrower_name}")
        c.drawString(50, height - 165, f"Application ID: {application_id}")
        c.drawString(50, height - 185, f"Loan Amount: {formatted_amount}")
        c.drawString(50, height - 205, f"Interest Rate: {formatted_rate}")

        # -------------------------------------------------
        # 📜 TERMS
        # -------------------------------------------------
        terms = [
            "1. Loan must be repaid as per EMI schedule.",
            "2. Late payment penalty applies.",
            "3. Pre-closure allowed after 3 EMIs.",
            "4. Processing fee is non-refundable.",
            "5. This is a system-generated legal document.",
        ]

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 250, "Loan Terms & Conditions")

        c.setFont("Helvetica", 11)
        y = height - 280
        for t in terms:
            c.drawString(60, y, t)
            y -= 18

        # -------------------------------------------------
        # ✍️ SIGNATURES
        # -------------------------------------------------
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 150, "Borrower Signature: ____________________________")
        c.drawString(50, 120, "Lender Authority Signature: _____________________")

        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, 30, "This is a system-generated document.")

        c.showPage()
        c.save()

        return {
            "file_path": str(file_path),
            "file_name": file_name
        }

    # =====================================================
    # 🔐 HASH GENERATION
    # =====================================================
    def generate_hash(self, file_path: str):
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()