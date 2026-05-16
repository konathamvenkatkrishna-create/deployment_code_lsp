from core.email_service import EmailService
from io import BytesIO
import asyncio
from routers.Repayment.loan_closure import loan_closure_pdf
from routers.Repayment.loan_closure import credit_bureau_pdf
from routers.Repayment.ndc import dowmload_ndc


async def send_loan_completion_docs(application_id, email, db):

    

    # Generate PDFs
    closure_pdf = loan_closure_pdf(application_id, db)
    credit_pdf  = credit_bureau_pdf(application_id, db)
    ndc_pdf     = dowmload_ndc(application_id, db)

    # NOTE: If these return StreamingResponse,
    # you may need to refactor to return bytes instead

    asyncio.create_task(
        EmailService.send_email_with_attachment(
            to_email=email,
            subject="Loan Closure Documents",
            body="Attached: Loan Closure, Credit Report & NDC",
            file_bytes=closure_pdf.body,
            filename=f"loan_closure_{application_id}.pdf"
        )
    )