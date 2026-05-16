from models.Consent.consent_master import ConsentMaster
def seed_doc(db, type, version, content):
    """Insert only if the type does NOT already exist."""
    exists = db.query(ConsentMaster).filter_by(type=type).first()
    if exists:
        return
    doc = ConsentMaster(
        type=type,
        version=version,
        content=content,
        active=True
    )
    db.add(doc)
    db.commit()
DATA_CONSENT_TEXT = """
YOUR CONSENT REQUIRED

We will collect and use the following information as part of your loan onboarding process:

1. Personal Details  
   - Full Name  
   - Date of Birth  
   - Address  

2. Financial Details  
   - Income information  
   - Bank account details  

3. Employment Details  
   - Company name  
   - Monthly salary  

4. Identity Documents  
   - PAN  
   - Aadhaar  

5. Credit Bureau Report (CIBIL/Equifax/Experian/CRIF)

Purpose of Collection:
- To process and assess your loan application  
- To verify your identity  
- To determine your creditworthiness  
- To comply with RBI regulatory requirements  

Data Sharing:
- NBFC Partner: [NBFC Partner Name], RBI Registered (Reg. No: XXXX)
- Credit Information Companies (CIBIL/CRIF/Equifax/Experian)

Your Rights:
- You may withdraw consent anytime  
- You may request deletion of your data after loan closure  
- You may request access to your stored data  

By clicking 'I Agree', you give explicit consent for the above.
"""

TERMS_AND_CONDITIONS_TEXT = """
TERMS & CONDITIONS (RBI Compliant)

1. You authorize our platform and NBFC partner to verify your identity and financial information.  
2. You agree that the information provided by you is accurate and may be used for loan assessment.  
3. You acknowledge that consent is required to proceed with the loan application.  
4. You accept that your information may be shared with the NBFC partner and credit bureaus.  
5. You agree that the decision to approve or reject the loan lies solely with the NBFC partner.  
6. Violations or misuse of the application may result in account suspension.

Scroll to the bottom and explicitly click "I Accept" to proceed.
"""

PRIVACY_POLICY_TEXT = """
PRIVACY POLICY

Data We Collect:
- Personal details (name, DOB, address)
- Financial data (income, bank account)
- KYC documents (PAN, Aadhaar)
- Employment information
- Credit bureau reports

Data Protection:
- Your data is encrypted and stored securely.
- Access is strictly limited to authorized personnel.

Data Sharing:
- NBFC partner for loan processing
- RBI-regulated Credit Information Companies

User Rights:
- Right to withdraw consent
- Right to data access
- Right to data deletion after loan closure

 Contact:
 For any privacy concerns, contact support@lsp.com
"""

CREDIT_BUREAU_CONSENT_TEXT = """
CREDIT BUREAU CONSENT

You authorize our platform and NBFC partner to fetch your credit bureau report from:
- CIBIL
- Equifax
- CRIF Highmark
- Experian

Hard Pull vs Soft Pull:
- A SOFT PULL does NOT affect your credit score.
- A HARD PULL MAY affect your credit score based on the lender’s request.

By selecting "I Agree", you explicitly consent to the retrieval of your credit report for loan assessment.
"""
def seed_all(db):
    seed_doc(db, "Data Consent", "v1.0", DATA_CONSENT_TEXT)
    seed_doc(db, "Terms & Conditions", "v1.0", TERMS_AND_CONDITIONS_TEXT)
    seed_doc(db, "Privacy Policy", "v1.0", PRIVACY_POLICY_TEXT)
    seed_doc(db, "Credit Bureau Consent", "v1.0", CREDIT_BUREAU_CONSENT_TEXT)



