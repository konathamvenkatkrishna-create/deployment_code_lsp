from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from datetime import datetime
import os


def generate_ndc_pdf(
    file_path: str,
    borrower_name: str,
    loan_id: int,
    application_id: int,
    lender_name: str = "ABC Finance Ltd"
):
    """
    Generates No Due Certificate PDF
    """

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    # =====================================================
    # 🏢 HEADER
    # =====================================================
    elements.append(Paragraph(f"<b>{lender_name}</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>No Due Certificate (NDC)</b>", styles["Heading2"]))
    elements.append(Spacer(1, 20))

    # =====================================================
    # 📄 BODY TEXT
    # =====================================================
    text = f"""
    This is to certify that <b>{borrower_name}</b> has successfully repaid the loan 
    bearing Application ID <b>{application_id}</b> and Loan ID <b>{loan_id}</b> 
    in full.

    As per our records, there are <b>no outstanding dues</b> against this loan.

    The loan account is hereby marked as <b>CLOSED</b>.
    """

    elements.append(Paragraph(text, styles["Normal"]))
    elements.append(Spacer(1, 20))

    # =====================================================
    # 📊 SUMMARY TABLE
    # =====================================================
    table_data = [
        ["Borrower Name", borrower_name],
        ["Loan ID", str(loan_id)],
        ["Application ID", str(application_id)],
        ["Status", "CLOSED"],
        ["Issued Date", datetime.utcnow().strftime("%Y-%m-%d")]
    ]

    table = Table(table_data, colWidths=[2.5 * inch, 3.5 * inch])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 40))

    # =====================================================
    # ✍️ SIGNATURE
    # =====================================================
    elements.append(Paragraph("Authorized Signatory", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(lender_name, styles["Normal"]))

    # =====================================================
    # 📄 BUILD PDF
    # =====================================================
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    doc.build(elements)

    return file_path