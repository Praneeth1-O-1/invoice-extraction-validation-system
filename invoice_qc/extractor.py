"""
PDF invoice extraction module.
Extracts structured data from invoice PDFs with English logic.
"""

import re
import pdfplumber
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from .schemas import Invoice, LineItem, Currency


class InvoiceExtractor:
    """Extracts structured invoice data from English PDF files"""

    def __init__(self):
        # Default extraction patterns for English invoices
        self.patterns = {
            "invoice_number": [
                r"INVOICE\s*(?:#|Number|No\.?)\s*:?\s*([A-Z0-9\-\/]+)",
                r"Inv\.\s*No\.?\s*:?\s*([A-Z0-9\-\/]+)",
            ],
            "invoice_date": [
                r"DATE\s*:?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
                r"Invoice\s*Date\s*:?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
            ],
            "due_date": [
                r"Due\s*(?:after|by|date)\s*:?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
                r"Due\s*Date\s*:?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
            ],
            "po_number": [
                r"P\.?O\.?\s*(?:NUMBER|No\.?|#)\s*:?\s*([A-Z0-9\-\/]+)",
                r"Purchase\s*Order\s*:?\s*([A-Z0-9\-\/]+)",
            ],
            "payment_terms": [
                r"TERMS\s*:?\s*([^\n]+)",
                r"Payment\s*Terms\s*:?\s*([^\n]+)",
            ],
        }

        self.currency_symbols = {
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
            "₹": "INR",
        }

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

        # Invoice number
        data["invoice_number"] = self._extract_with_patterns(text, self.patterns["invoice_number"])

        # Invoice date
        invoice_date_str = self._extract_with_patterns(text, self.patterns["invoice_date"])
        if invoice_date_str:
            data["invoice_date"] = self._parse_date(invoice_date_str)

        # Due date
        # Check for relative due date text first (e.g. "Due after 30 days")
        due_text = self._extract_with_patterns(text, self.patterns["payment_terms"])
        if due_text and "days" in due_text.lower():
            # Logic to calculate due date could go here, but for now we look for explicit dates
            pass
            
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
            "%d.%m.%Y", "%m.%d.%Y",  # Dot separators
            "%Y-%m-%d", "%d-%m-%Y",  # Dash separators
            "%d/%m/%Y", "%m/%d/%Y",  # Slash separators
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

        # ------------------------------------------------------------------
        # Heuristic: Seller is often at the top-left or centered at top.
        # We look at the first few non-empty lines, skipping known headers.
        
        lines = text.split('\n')
        seller_lines = []
        
        # Stop-words that indicate we've moved past the header/branding area
        header_stop_patterns = [
            r"^(?:TO|BILL TO|SHIP TO|SOLD TO|BILLED TO):", 
            r"^INVOICE\s*(?:#|NO|NUMBER)", 
            r"^DATE:", 
            r"^PAGE",
            r"^DETAILS"
        ]
        
        for line in lines[:20]: # Only check top section
            line = line.strip()
            if not line:
                continue
                
            # Skip generic document titles if they appear alone
            if re.match(r"^(?:INVOICE|TAX INVOICE|CREDIT NOTE)$", line, re.IGNORECASE):
                continue

            # Check if we hit a stop section
            if any(re.search(p, line, re.IGNORECASE) for p in header_stop_patterns):
                break
                
            seller_lines.append(line)
        
        # Filter metadata from collected seller lines (e.g. if Date appears on same line)
        cleaned_seller_lines = []
        for l in seller_lines:
             # Basic filter: if line looks like a date or invoice number, skip/clean it
             # But usually top lines are Name, Address, Phone.
             if re.search(r"INVOICE\s*#", l, re.IGNORECASE): continue
             cleaned_seller_lines.append(l)

        if cleaned_seller_lines:
            data["seller_name"] = cleaned_seller_lines[0]
            if len(cleaned_seller_lines) > 1:
                data["seller_address"] = " ".join(cleaned_seller_lines[1:4])


        # ------------------------------------------------------------------
        # BUYER Extraction
        # ------------------------------------------------------------------
        # Look for "TO" or "BILL TO" blocks.
        
        # We'll search for the keyword, then capture lines immediately following it.
        # Regex explanation:
        # (?:\bTO\b|BILL TO|SOLD TO|BILLED TO)  --> Trigger words
        # \s*[:\-]?\s*                          --> Separator (optional)
        # (.*?)                                 --> Capture content (lazy)
        # (?=\n\s*\n|\bSHIP TO\b|\bINVOICE\b|...) --> Stop text (Lookahead)
        
        buyer_keywords = r"(?:\bTO\b|BILL TO|SOLD TO|BILLED TO|CUSTOMER)"
        
        # Find all start positions
        matches = list(re.finditer(buyer_keywords, text, re.IGNORECASE))
        
        if matches:
            # Usually the first match is the main Bill-To
            match = matches[0]
            start_idx = match.end()
            
            # Special case: check if there is text on the SAME line after the colon
            # e.g. "Bill To: Acme Corp"
            # match.end() gives index after "Bill To", we check up to newline
            next_newline = text.find('\n', start_idx)
            same_line_content = text[start_idx:next_newline].strip(" :-\t")
            
            buyer_candidates = []
            
            if same_line_content:
                buyer_candidates.append(same_line_content)
                # Then grab subsequent lines
                search_start = next_newline
            else:
                search_start = start_idx
            
            # Grab next chunk of lines
            chunk = text[search_start:search_start+500]
            chunk_lines = chunk.split('\n')
            
            for line in chunk_lines:
                line = line.strip()
                if not line:
                    # Allow 1 empty line gap, but stop at second? 
                    # Actually standard invoice blocks are contiguous.
                    # If we already have candidates and hit empty, we might stop or continue depending on layout.
                    # For safety, if we have a name, empty line might mean end of block.
                    if buyer_candidates:
                        break # Assume block end
                    continue
                
                # Check for stop keywords (other sections)
                if re.search(r"(SHIP TO|INVOICE|DATE|QUANTITY|DESCRIPTION|ITEM|TOTAL|PAYMENT)", line, re.IGNORECASE):
                    break
                    
                buyer_candidates.append(line)
            
            if buyer_candidates:
                data["buyer_name"] = buyer_candidates[0]
                if len(buyer_candidates) > 1:
                    data["buyer_address"] = " ".join(buyer_candidates[1:])

        # Fallback: Validation often requires both names. 
        # If we failed to find specific "TO" block, but have text, maybe we missed it.
        # But heuristic is safer than guessing random lines.

        return data

    # ----------------------------------------------------------------------
    # CURRENCY & AMOUNTS
    # ----------------------------------------------------------------------
    def _extract_currency(self, text: str) -> Optional[str]:
        # Check symbols first
        for symbol, code in self.currency_symbols.items():
            if symbol in text:
                return code
        
        # Check codes
        for currency in Currency:
            if re.search(r"\b" + currency.value + r"\b", text, re.IGNORECASE):
                return currency.value

        return "USD"

    def _extract_amounts(self, text: str) -> Dict[str, Any]:
        data = {}

        def clean_number(s: str) -> Optional[Decimal]:
            if not s:
                return None
            # Standard English: remove characters that aren't digits or dots
            # Note: Dealing with thousands separators (commas) by removing them
            cleaned = re.sub(r"[^0-9\.]", "", s.replace(',', ''))
            try:
                return Decimal(cleaned)
            except:
                return None

        # Helper to find values associated with keys at end of lines
        # e.g. "TOTAL DUE 576.95" or "TOTAL DUE: 576.95"
        def find_value(keys: List[str]) -> Optional[Decimal]:
            for key in keys:
                # Pattern: Key followed optionally by colon/symbol, then number at END of line or text
                pattern = r"(?:" + "|".join(keys) + r")\s*[:$€]?\s*([\d,\.]+)"
                # We want the match that is likely the final amount, not a line item description
                # Searching line by line is safer for totals usually at the bottom
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                if matches:
                    # Take the last match as totals usually appear at bottom
                    return clean_number(matches[-1].group(1))
            return None

        # Gross Total
        # Prioritize specific "Total Due" labels over generic "Total"
        gross = find_value(["TOTAL DUE", "AMOUNT DUE", "TOTAL PAYABLE", "GRAND TOTAL"])
        if gross:
            data["gross_total"] = gross
        else:
            # Fallback to just "TOTAL" but be careful not to pick up column header
            # Regex ensures it matches a number
            match = re.search(r"\bTOTAL\s*[:$€]?\s*([\d,\.]+)", text, re.IGNORECASE)
            if match:
                 # Verify it's not the header "TOTAL" which usually isn't followed immediately by a number
                 data["gross_total"] = clean_number(match.group(1))

        # Subtotal
        sub = find_value(["SUBTOTAL", "SUB TOTAL", "NET TOTAL"])
        if sub:
            data["net_total"] = sub

        # Tax
        tax = find_value(["SALES TAX", "TAX", "VAT", "TOTAL TAX"])
        if tax:
            data["tax_amount"] = tax

        # Heuristic: If we have Gross and Tax but no Net, or combinations
        if data.get("gross_total") and data.get("tax_amount") and not data.get("net_total"):
            data["net_total"] = data["gross_total"] - data["tax_amount"]

        return data

    # ----------------------------------------------------------------------
    # LINE ITEMS
    # ----------------------------------------------------------------------
    def _extract_line_items(self, pdf) -> List[Dict[str, Any]]:
        line_items = []

        try:
            # Strategy 1: Table Extraction (Works if PDF has grid lines)
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    header = table[0]
                    desc_col = self._find_column_index(header, ["description", "item", "product", "details"])
                    qty_col = self._find_column_index(header, ["qty", "quantity", "count"])
                    price_col = self._find_column_index(header, ["unit price", "price", "rate", "cost", "unit"])
                    total_col = self._find_column_index(header, ["total", "amount", "extension"])
                    
                    # If we found at least a description column
                    if desc_col is not None:
                         for row in table[1:]:
                            if not row: continue
                            
                            # Clean row content
                            clean_row = [str(c).strip() if c else "" for c in row]
                            
                            # Skip header repetition or footer
                            if "total" in clean_row[0].lower(): continue

                            item = {}
                            item["description"] = clean_row[desc_col].replace('\n', ' ')
                            
                            if qty_col is not None:
                                try: item["quantity"] = float(clean_row[qty_col].replace(',', ''))
                                except: pass
                            
                            if price_col is not None:
                                try: item["unit_price"] = Decimal(re.sub(r"[^0-9\.]", "", clean_row[price_col]))
                                except: pass
                                
                            if total_col is not None:
                                try: item["line_total"] = Decimal(re.sub(r"[^0-9\.]", "", clean_row[total_col]))
                                except: pass
                            
                            if item.get("description") and (item.get("line_total") or item.get("quantity")):
                                line_items.append(item)
            
            # Strategy 2: Text-based Regex fallback (if tables failed)
            if not line_items:
                full_text = ""
                for page in pdf.pages:
                     # Layout=True helps preserve horizontal positioning
                     full_text += page.extract_text(layout=True) + "\n"
                
                # Simple pattern: Quantity (number) ... Description (text) ... Price (number) ... Total (number)
                # This is fragile but handles the "no grid lines" case better
                # Look for lines starting with a number (quantity)
                lines = full_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    # Regex: Start with Number (Qty), space, Description, space, Number (Price), space, Number (Total)
                    # 10 Dextromethorphan polistirex 12.45 124.50
                    match = re.search(r"^(\d+(?:\.\d+)?)\s+(.+?)\s+(\d+\.\d{2})\s+(\d+\.\d{2})$", line)
                    if match:
                        qty, desc, price, total = match.groups()
                        # Filter out things that look like dates or random numbers
                        if " " not in desc and len(desc) < 3: continue 
                        
                        line_items.append({
                            "quantity": float(qty),
                            "description": desc.strip(),
                            "unit_price": Decimal(price),
                            "line_total": Decimal(total)
                        })

        except Exception as e:
            print(f"Error extracting line items: {e}")

        return line_items

    def _find_column_index(self, header: List, keywords: List[str]) -> Optional[int]:
        for i, cell in enumerate(header):
            if cell:
                cell_lower = str(cell).lower().replace('\n', ' ')
                for keyword in keywords:
                    if keyword == cell_lower or keyword in cell_lower:
                        return i
        return None
