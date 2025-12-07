"""
PDF invoice extraction module.
Extracts structured data from invoice PDFs with German → English normalization.
"""

import re
import pdfplumber
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from .schemas import Invoice, LineItem, Currency


class InvoiceExtractor:
    """Extracts structured invoice data from PDF files"""

    def __init__(self):
        # German → English keyword normalization map
        self.keyword_map = {
            "Rechnung": "Invoice",
            "Rechnungsnummer": "Invoice Number",
            "Rechnungsdatum": "Invoice Date",
            "Datum": "Date",
            "Lieferdatum": "Delivery Date",
            "Bestellnummer": "Order Number",
            "Bestellung": "Order",
            "Gesamtwert inkl. MwSt": "Total Including Tax",
            "Gesamtwert": "Total",
            "MwSt": "VAT",
            "Zahlungsbedingungen": "Payment Terms",
            "Kostenstelle": "Cost Center",
            "Lief.Art.Nr": "Item Number",
            "Sterilisationsmittel": "Sterilization Agent",
            "Beispielname Unternehmen": "Example Company",
        }

        # Default extraction patterns
        self.patterns = {
            "invoice_number": [
                r"Invoice\s*(?:Number|No\.?|#)\s*:?\s*([A-Z0-9\-\/]+)",
                r"Order\s*(?:Number|No\.?|#)\s*:?\s*([A-Z0-9\-\/]+)",
            ],
            "invoice_date": [
                r"Invoice\s*Date\s*:?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
                r"Date\s*:?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
            ],
            "due_date": [
                r"Due\s*Date\s*:?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
            ],
            "po_number": [
                r"(?:PO|Purchase\s*Order)\s*(?:Number|No\.?)\s*:?\s*([A-Z0-9\-]+)",
            ],
            "payment_terms": [
                r"Payment\s*Terms\s*:?\s*([^\n]+)",
            ],
        }

        self.currency_symbols = {
            "€": "EUR",
            "$": "USD",
            "£": "GBP",
            "₹": "INR",
        }

    # ----------------------------------------------------------------------
    # NORMALIZATION
    # ----------------------------------------------------------------------
    def _normalize_keywords(self, text: str) -> str:
        """Replace German keywords with English equivalents."""
        normalized = text
        for german, english in self.keyword_map.items():
            normalized = normalized.replace(german, english)
        return normalized

    # ----------------------------------------------------------------------
    # EXTRACTION ENTRY POINTS
    # ----------------------------------------------------------------------
    def extract_from_directory(self, pdf_dir: Path) -> List[Invoice]:
        pdf_dir = Path(pdf_dir)
        invoices = []

        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                invoice = self.extract_from_pdf(pdf_file)
                if invoice:
                    invoices.append(invoice)
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {e}")

        return invoices

    def extract_from_pdf(self, pdf_path: Path) -> Optional[Invoice]:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        full_text += extracted + "\n"

                # Normalize German → English labels
                full_text = self._normalize_keywords(full_text)

                # Parse structured data
                invoice_data = self._parse_invoice_text(full_text)
                invoice_data["source_file"] = pdf_path.name

                # Extract line items
                line_items = self._extract_line_items(pdf)
                if line_items:
                    invoice_data["line_items"] = line_items

                return Invoice(**invoice_data)

        except Exception as e:
            print(f"Error extracting from {pdf_path}: {e}")
            return None

    # ----------------------------------------------------------------------
    # CORE PARSING
    # ----------------------------------------------------------------------
    def _parse_invoice_text(self, text: str) -> Dict[str, Any]:
        data = {}

        # Invoice number (English style)
        data["invoice_number"] = self._extract_with_patterns(text, self.patterns["invoice_number"])

        # --- NEW AUFNR invoice number extraction ---
        if not data.get("invoice_number"):
            m = re.search(r"AUFNR\s*([0-9]+)", text)
            if m:
                data["invoice_number"] = m.group(1)

        # Invoice date
        invoice_date_str = self._extract_with_patterns(text, self.patterns["invoice_date"])
        if invoice_date_str:
            data["invoice_date"] = self._parse_date(invoice_date_str)

        # Fallback German-style date (dd.mm.yyyy)
        if not data.get("invoice_date"):
            m = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
            if m:
                data["invoice_date"] = self._parse_date(m.group(1))

        # Due date
        due_date_str = self._extract_with_patterns(text, self.patterns["due_date"])
        if due_date_str:
            data["due_date"] = self._parse_date(due_date_str)

        # PO / external reference
        data["external_reference"] = self._extract_with_patterns(text, self.patterns["po_number"])

        # Payment terms
        data["payment_terms"] = self._extract_with_patterns(text, self.patterns["payment_terms"])

        # Seller/buyer extraction
        parties = self._extract_parties(text)
        data.update(parties)

        # Currency
        data["currency"] = self._extract_currency(text)

        # Financial amounts
        amounts = self._extract_amounts(text)
        data.update(amounts)

        return data


    # ----------------------------------------------------------------------
    # REGEX HELPERS
    # ----------------------------------------------------------------------
    def _extract_with_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        date_formats = [
            "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y",
            "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y",
            "%m/%d/%y", "%d.%m.%y",
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date().isoformat()
            except ValueError:
                continue
        return None

    # ----------------------------------------------------------------------
    # PARTY EXTRACTION
    # ----------------------------------------------------------------------
    def _extract_parties(self, text: str) -> Dict[str, Any]:
        data = {}

        # Improved seller detection for German-style invoices
        # Extract seller block (English-normalized)
        # Seller = text before 'Order AUFNR'
        seller_match = re.search(r"(.+?)\s+Order\s+AUFNR", text)
        if seller_match:
            data["seller_name"] = seller_match.group(1).strip()


        # Buyer detection fallback
        buyer_match = re.search(r"(Order[\s\S]{0,200})", text)
        if buyer_match:
            lines = [l.strip() for l in buyer_match.group(1).split("\n") if l.strip()]
            data["buyer_name"] = lines[0]

        return data

    # ----------------------------------------------------------------------
    # CURRENCY & AMOUNTS
    # ----------------------------------------------------------------------
    def _extract_currency(self, text: str) -> Optional[str]:
        for currency in Currency:
            if re.search(r"\b" + currency.value + r"\b", text, re.IGNORECASE):
                return currency.value

        for symbol, code in self.currency_symbols.items():
            if symbol in text:
                return code

        return None

    def _extract_amounts(self, text: str) -> Dict[str, Any]:
        data = {}

        def clean_number(s: str) -> Optional[Decimal]:
            if not s:
                return None
            # Remove everything except digits, comma, dot
            cleaned = re.sub(r"[^0-9\.,]", "", s)
            # Fix German format
            cleaned = cleaned.replace(".", "").replace(",", ".")
            try:
                return Decimal(cleaned)
            except:
                return None

        # Total Including Tax
        gross_match = re.search(
            r"Total Including Tax[^0-9]*([\d\.,]+)",
            text,
            re.IGNORECASE,
        )
        if gross_match:
            data["gross_total"] = clean_number(gross_match.group(1))

        # Fallback for Total
        if "gross_total" not in data:
            total_match = re.search(
                r"Total[^0-9]*([\d\.,]+)",
                text,
                re.IGNORECASE,
            )
            if total_match:
                data["gross_total"] = clean_number(total_match.group(1))

        return data


    # ----------------------------------------------------------------------
    # LINE ITEMS
    # ----------------------------------------------------------------------
    def _extract_line_items(self, pdf) -> List[Dict[str, Any]]:
        line_items = []

        try:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    header = table[0]
                    desc_col = self._find_column_index(header, ["description", "item", "product"])
                    qty_col = self._find_column_index(header, ["qty", "quantity", "menge"])
                    price_col = self._find_column_index(header, ["price", "unit price", "preis"])
                    total_col = self._find_column_index(header, ["total", "amount", "betrag"])

                    for row in table[1:]:
                        if not row or all(not cell or str(cell).strip() == "" for cell in row):
                            continue

                        item = {}

                        if desc_col is not None:
                            item["description"] = str(row[desc_col]).strip()

                        if qty_col is not None:
                            try:
                                item["quantity"] = float(row[qty_col])
                            except:
                                pass

                        if price_col is not None and row[price_col]:
                            try:
                                price_str = str(row[price_col]).replace(",", ".")
                                item["unit_price"] = Decimal(price_str)
                            except:
                                pass

                        if total_col is not None and row[total_col]:
                            try:
                                total_str = str(row[total_col]).replace(",", ".")
                                item["line_total"] = Decimal(total_str)
                            except:
                                pass

                        if item:
                            line_items.append(item)

        except Exception as e:
            print(f"Error extracting line items: {e}")

        return line_items

    def _find_column_index(self, header: List, keywords: List[str]) -> Optional[int]:
        for i, cell in enumerate(header):
            if cell:
                cell_lower = str(cell).lower()
                for keyword in keywords:
                    if keyword in cell_lower:
                        return i
        return None
