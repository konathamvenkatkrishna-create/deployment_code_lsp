import re
import os
import cv2
import numpy as np
import pytesseract
from rapidfuzz import fuzz

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class KYCService:

    @staticmethod
    def _extract_text_from_pdf_direct(path: str) -> str:
        """
        Extract text directly from text-based PDFs using PyMuPDF.
        Much faster and more accurate than Tesseract for non-scanned PDFs.
        Returns empty string if PDF is image-based (fallback to Tesseract).
        """
        try:
            import fitz
            doc  = fitz.open(path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception:
            return ""

    @staticmethod
    def _pdf_to_images(path: str) -> list:
        """
        Convert PDF pages to grayscale numpy arrays for Tesseract OCR.
        Used as fallback for scanned / image-based PDFs.
        """
        try:
            import fitz
        except ImportError:
            raise Exception("PyMuPDF not installed. Run: pip install pymupdf")
        doc    = fitz.open(path)
        images = []
        for page in doc:
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
            images.append(arr)
        doc.close()
        return images

    @staticmethod
    def _preprocess_gray(gray: np.ndarray) -> np.ndarray:
        h, w = gray.shape[:2]
        if w < 1500:
            scale = 1500 / w
            gray  = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray   = cv2.fastNlMeansDenoising(gray, h=10)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 10,
        )
        return thresh

    # =========================================================================
    # TEXT EXTRACTION
    # =========================================================================

    @staticmethod
    def extract_text(path: str, lang: str = "eng") -> str:
        ext = os.path.splitext(path)[1].lower()

        if ext == ".pdf":
            # Step 1: Try direct text extraction (text-based PDFs — salary slips, bank statements)
            direct_text = KYCService._extract_text_from_pdf_direct(path)
            if direct_text and len(direct_text) > 50:
                # PDF has embedded text — use it directly, no Tesseract needed
                return direct_text

            # Step 2: Fallback to Tesseract for scanned / image-based PDFs
            pages    = KYCService._pdf_to_images(path)
            all_text = []
            for gray in pages:
                thresh = KYCService._preprocess_gray(gray)
                text   = pytesseract.image_to_string(thresh, lang=lang, config="--oem 3 --psm 6")
                all_text.append(text)
            return "\n".join(all_text)

        # ── Image files (JPG / PNG) ───────────────────────────────────────────
        img = cv2.imread(path)
        if img is None:
            raise Exception(f"Image not readable: {path}")

        h, w = img.shape[:2]
        if w < 1500:
            scale = 1500 / w
            img   = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        gray   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray   = cv2.fastNlMeansDenoising(gray, h=10)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 10,
        )
        return pytesseract.image_to_string(thresh, lang=lang, config="--oem 3 --psm 6")

    # =========================================================================
    # SHARED UTILITIES
    # =========================================================================

    @staticmethod
    def normalize_name(name: str) -> str:
        if not name:
            return ""
        name = name.upper()
        name = re.sub(r'[^A-Z\s]', '', name)
        return re.sub(r'\s+', ' ', name).strip()

    @staticmethod
    def name_match(n1: str, n2: str):
        n1    = KYCService.normalize_name(n1)
        n2    = KYCService.normalize_name(n2)
        if not n1 or not n2:
            return False, 0
        score = fuzz.token_sort_ratio(n1, n2)
        return score > 80, score

    @staticmethod
    def _normalize_dob(dob_value) -> str | None:
        if dob_value is None:
            return None
        if hasattr(dob_value, 'day'):
            return f"{dob_value.day:02d}/{dob_value.month:02d}/{dob_value.year}"
        s = str(dob_value).strip()
        m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s)
        if m:
            return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
        m = re.fullmatch(r'(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})', s)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
        return None

    @staticmethod
    def _extract_best_name(raw_line: str, user_name: str) -> str:
        clean  = re.sub(r'[^A-Za-z\s]', ' ', raw_line)
        clean  = re.sub(r'\s+', ' ', clean).strip()
        tokens = [w.upper() for w in clean.split() if len(w) >= 2]

        if not tokens:
            return ""

        user_words = KYCService.normalize_name(user_name).split()
        max_window = min(len(tokens), len(user_words) + 2)

        best_name  = " ".join(tokens)
        best_score = 0

        for size in range(1, max_window + 1):
            for start in range(len(tokens) - size + 1):
                window   = " ".join(tokens[start : start + size])
                _, score = KYCService.name_match(user_name, window)
                if score > best_score:
                    best_score = score
                    best_name  = window

        return best_name if best_score >= 40 else " ".join(tokens)

    @staticmethod
    def _is_label_line(line: str) -> bool:
        label_patterns = [
            r'\bName\b', r'\bFather\b', r'\bBirth\b', r'\bDOB\b',
            r'\bDate\b', r'\bSign\b', r'\bIncome\b', r'\bTax\b',
            r'\bDepartment\b', r'\bPermanent\b', r'\bAccount\b',
            r'\bNumber\b', r'\bGovt\b', r'\bGovernment\b', r'\bIndia\b',
            r'\bUIDAI\b', r'\bUnique\b', r'\bIdentification\b',
            r'\bAuthority\b', r'\bEnrollment\b', r'\bVID\b',
            r'[^\x00-\x7F]',
        ]
        for pat in label_patterns:
            if re.search(pat, line, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def _next_value_line(lines: list, from_index: int) -> tuple:
        for i in range(from_index, min(from_index + 3, len(lines))):
            line = lines[i].strip()
            if line and not KYCService._is_label_line(line):
                return i, line
        return -1, ''

    @staticmethod
    def _extract_name_from_financial_doc(full_text: str) -> str:
        """
        Extract employee / account holder name from a financial document.
        Tries priority-ordered label patterns.
        Returns uppercase name string, or "" if nothing found.
        """
        SEP = r'[\s=]*[:\-][\s=]*'

        name_patterns = [
            # Salary slip specific (tried first)
            rf'Employee\s*Name{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            rf'Name\s*of\s*Employee{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            rf'Staff\s*Name{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            rf'Worker\s*Name{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            # Bank statement specific
            rf'Account\s*Holder\s*(?:Name)?{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            rf'A/?C\s*Holder\s*(?:Name)?{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            rf'Customer\s*Name{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            # Common to both
            rf'(?:Pay\s*To|Beneficiary){SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
            rf'(?:^|\n)\s*Name{SEP}([A-Za-z][A-Za-z\s\.]{{1,50}})',
        ]

        for pattern in name_patterns:
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                candidate = re.split(
                    r'\n|\r|(?:\s{2,})|(?:Account|Address|Branch|IFSC|Date|Balance|Number|Code|Department|Designation|Salary|Basic)',
                    candidate, flags=re.IGNORECASE
                )[0]
                candidate = re.sub(r'[^A-Za-z\s]', '', candidate).strip()
                if len(candidate) >= 3 and not re.match(
                    r'^(Account|Branch|IFSC|Balance|Number|Date|Statement|Department|Designation)$',
                    candidate, re.IGNORECASE
                ):
                    return candidate.upper()

        return ""

    # =========================================================================
    # PAN CARD
    # verified: pan_number + name  vs  user.pan_number + user.full_name
    # =========================================================================

    @staticmethod
    def process_pan(text: str, user) -> dict:
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        pan        = None
        pan_line_i = None
        for i, line in enumerate(lines):
            m = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', line)
            if m:
                pan        = m.group(1)
                pan_line_i = i
                break

        name_label_i   = -1
        father_label_i = -1
        dob_label_i    = -1

        search_from = pan_line_i + 1 if pan_line_i is not None else 0

        for i in range(search_from, len(lines)):
            line_up = lines[i].upper()
            if name_label_i == -1 and re.search(r'\bNAME\b', line_up) and 'FATHER' not in line_up:
                name_label_i = i
            if father_label_i == -1 and re.search(r'\bFATHER\b', line_up):
                father_label_i = i
            if dob_label_i == -1 and re.search(r'\b(BIRTH|DATE OF BIRTH|DOB)\b', line_up):
                dob_label_i = i

        extracted_name = ""
        father_name    = ""

        if name_label_i != -1:
            _, raw = KYCService._next_value_line(lines, name_label_i + 1)
            if raw:
                extracted_name = KYCService._extract_best_name(raw, user.full_name)

        if father_label_i != -1:
            _, raw = KYCService._next_value_line(lines, father_label_i + 1)
            if raw:
                father_name = KYCService._extract_best_name(raw, user.full_name)

        if extracted_name and father_name and extracted_name == father_name:
            extracted_name = ""

        if not extracted_name and pan_line_i is not None:
            for i in range(pan_line_i + 1, len(lines)):
                line = lines[i].strip()
                if KYCService._is_label_line(line):
                    continue
                if re.search(r'\d', line):
                    continue
                best = KYCService._extract_best_name(line, user.full_name)
                if not best:
                    continue
                if father_name and best == father_name:
                    continue
                extracted_name = best
                break

        pan_dob = None
        if dob_label_i != -1:
            _, raw = KYCService._next_value_line(lines, dob_label_i + 1)
            m = re.search(r'\b(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})\b', raw)
            if m:
                pan_dob = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"

        if not pan_dob:
            for line in lines:
                m = re.search(r'\b(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})\b', line)
                if m:
                    pan_dob = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
                    break

        pan_match      = (pan == user.pan_number) if pan and user.pan_number else False
        matched, score = KYCService.name_match(user.full_name, extracted_name)

        failed_reasons = []
        if not pan_match:
            failed_reasons.append(
                f"PAN number mismatch: extracted '{pan}', expected '{user.pan_number}'"
            )
        if not matched:
            failed_reasons.append(
                f"Name mismatch: extracted '{extracted_name}', "
                f"expected '{user.full_name}' (score: {round(score, 1)})"
            )

        return {
            "extracted": {
                "pan_number": pan,
                "name":       extracted_name,
                "dob":        pan_dob,
            },
            "comparison": {
                "pan_match":  pan_match,
                "name_match": matched,
                "name_score": round(score, 2),
                "verified":   pan_match and matched,
            },
            "user_data": {
                "pan_number": user.pan_number,
                "full_name":  user.full_name,
            },
            "failed_reasons": failed_reasons,
        }

    # =========================================================================
    # AADHAAR FRONT
    # verified: aadhaar_number + dob  vs  user.aadhaar_number + user.dob
    # =========================================================================

    @staticmethod
    def process_aadhaar(text: str, user) -> dict:
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        aadhaar = None
        for line in lines:
            m = re.search(r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b', line)
            if m:
                candidate = re.sub(r'[\s\-]', '', m.group())
                if len(candidate) == 12:
                    aadhaar = candidate
                    break

        dob = None
        for line in lines:
            if re.search(r'\b(DOB|Date\s*of\s*Birth|Birth|जन्म)\b', line, re.IGNORECASE):
                m = re.search(r'\b(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})\b', line)
                if m:
                    dob = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
                    break

        if not dob:
            for line in lines:
                m = re.search(r'\b(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})\b', line)
                if m:
                    dob = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
                    break

        yob = None
        if not dob:
            for line in lines:
                m = re.search(r'(?:Year\s*of\s*Birth|YOB)[:\s]*(\d{4})', line, re.IGNORECASE)
                if m:
                    yob = m.group(1)
                    break

        user_dob      = KYCService._normalize_dob(user.dob)
        aadhaar_match = (aadhaar == user.aadhaar_number) if aadhaar and user.aadhaar_number else False

        dob_match = False
        if dob and user_dob:
            dob_match = (dob == user_dob)
        elif yob and user.dob:
            year      = user.dob.year if hasattr(user.dob, 'year') else int(str(user.dob)[:4])
            dob_match = (yob == str(year))

        failed_reasons = []
        if not aadhaar_match:
            failed_reasons.append(
                f"Aadhaar number mismatch: extracted '{aadhaar}', expected '{user.aadhaar_number}'"
            )
        if not dob_match:
            extracted_dob_display = dob or (f"YOB:{yob}" if yob else "not found")
            failed_reasons.append(
                f"DOB mismatch: extracted '{extracted_dob_display}', expected '{user_dob}'"
            )

        return {
            "extracted": {
                "aadhaar_number": aadhaar,
                "dob":            dob or (f"YOB: {yob}" if yob else None),
            },
            "comparison": {
                "aadhaar_match": aadhaar_match,
                "dob_match":     dob_match,
                "verified":      aadhaar_match and dob_match,
            },
            "user_data": {
                "aadhaar_number": user.aadhaar_number,
                "dob":            user_dob,
            },
            "failed_reasons": failed_reasons,
        }

    # =========================================================================
    # AADHAAR BACK — auto-approved, no comparable data on back side
    # =========================================================================

    @staticmethod
    def process_aadhaar_back(text: str, user) -> dict:
        return {
            "extracted":      {},
            "comparison":     {"verified": True},
            "user_data":      {},
            "failed_reasons": [],
        }

    # =========================================================================
    # BANK STATEMENT
    # verified: account_number + name  vs  bank_verification (account + holder)
    # =========================================================================

    @staticmethod
    def process_bank(text: str, bank_verification) -> dict:
        lines     = [l.strip() for l in text.splitlines() if l.strip()]
        full_text = "\n".join(lines)

        # Extract account number
        acc          = None
        acc_patterns = [
            r'Account\s*(?:No\.?|Number)\s*[:\-]\s*(\d{9,18})',
            r'A/?C\s*(?:No\.?|Number)\s*[:\-]\s*(\d{9,18})',
            r'Acct\.?\s*(?:No\.?|Number)\s*[:\-]\s*(\d{9,18})',
            r'(?:SB|CA|OD|CC)\s*A/?C\s*[:\-]\s*(\d{9,18})',
        ]
        for pattern in acc_patterns:
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                acc = m.group(1)
                break

        if not acc:
            m = re.search(r'\b(\d{9,18})\b', full_text)
            if m:
                acc = m.group(1)

        # Extract name
        extracted_name = KYCService._extract_name_from_financial_doc(full_text)

        expected_account = bank_verification.account_number
        expected_name    = bank_verification.account_holder_name

        def normalize_account(v) -> str:
            if not v:
                return ""
            v = re.sub(r"[\s\-]", "", str(v))
            return v.lstrip("0") or "0"

        extracted_acc_norm = normalize_account(acc)
        expected_acc_norm  = normalize_account(expected_account)

        acc_match      = bool(extracted_acc_norm and expected_acc_norm and extracted_acc_norm == expected_acc_norm)
        matched, score = KYCService.name_match(expected_name or "", extracted_name)

        failed_reasons = []
        if not acc_match:
            failed_reasons.append(
                f"Account number mismatch: "
                f"extracted '{acc}' (normalized: '{extracted_acc_norm}'), "
                f"expected '{expected_account}' (normalized: '{expected_acc_norm}')"
            )
        if not matched:
            failed_reasons.append(
                f"Account holder name mismatch: extracted '{extracted_name}', "
                f"expected '{expected_name}' (score: {round(score, 1)})"
            )

        return {
            "extracted": {
                "account_number":            acc,
                "account_number_normalized": extracted_acc_norm,
                "name":                      extracted_name,
            },
            "comparison": {
                "account_match": acc_match,
                "name_match":    matched,
                "name_score":    round(score, 2),
                "verified":      acc_match and matched,
            },
            "user_data": {
                "account_number":            expected_account,
                "account_number_normalized": expected_acc_norm,
                "account_holder_name":       expected_name,
            },
            "failed_reasons": failed_reasons,
        }

    @staticmethod
    def process_salary_slip(text: str, user) -> dict:
        lines     = [l.strip() for l in text.splitlines() if l.strip()]
        full_text = "\n".join(lines)

        extracted_name = KYCService._extract_name_from_financial_doc(full_text)

        # Compare with PAN-verified profile name — not bank name
        expected_name  = user.full_name
        matched, score = KYCService.name_match(expected_name or "", extracted_name)

        failed_reasons = []
        if not matched:
            failed_reasons.append(
                f"Employee name mismatch: extracted '{extracted_name}', "
                f"expected '{expected_name}' (score: {round(score, 1)})"
            )

        return {
            "extracted": {
                "name": extracted_name,
            },
            "comparison": {
                "name_match": matched,
                "name_score": round(score, 2),
                "verified":   matched,
            },
            "user_data": {
                "full_name": expected_name,   # PAN-verified name
            },
            "failed_reasons": failed_reasons,
        }