"""
Invoice validation module.
Implements validation rules for invoice quality control.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Set
from .schemas import Invoice, ValidationResult, ValidationSummary, ValidationReport, Currency


class InvoiceValidator:
    """
    Validates invoices against defined business rules.
    
    Validation Rules Implemented:
    
    COMPLETENESS RULES (3+):
    1. invoice_number_required: Invoice must have a non-empty invoice number
    2. invoice_date_required: Invoice must have an invoice date
    3. parties_required: Seller and buyer names must not be empty
    4. amounts_required: Key financial amounts must be present
    
    BUSINESS RULES (2+):
    5. date_order: Due date must be on or after invoice date
    6. totals_consistency: Net total + tax amount should equal gross total (within tolerance)
    7. line_items_sum: Sum of line item totals should match net total (if line items present)
    8. non_negative_amounts: All amounts must be non-negative
    
    ANOMALY RULES (1+):
    9. duplicate_invoice: No duplicate invoices (same invoice number + seller)
    10. reasonable_date_range: Dates should be within reasonable range
    11. valid_currency: Currency must be from known set
    """
    
    def __init__(self, tolerance: float = 0.02):
        """
        Initialize validator.
        
        Args:
            tolerance: Tolerance for amount matching (e.g., 0.02 = 2% tolerance for rounding)
        """
        self.tolerance = tolerance
        self.seen_invoices: Set[tuple] = set()  # For duplicate detection
    
    def validate_batch(self, invoices: List[Invoice]) -> ValidationReport:
        """
        Validate a batch of invoices.
        
        Args:
            invoices: List of invoices to validate
            
        Returns:
            ValidationReport with summary and individual results
        """
        self.seen_invoices.clear()  # Reset for each batch
        results = []
        
        for invoice in invoices:
            result = self.validate_invoice(invoice)
            results.append(result)
        
        summary = self._create_summary(results)
        
        return ValidationReport(summary=summary, results=results)
    
    def validate_invoice(self, invoice: Invoice) -> ValidationResult:
        """
        Validate a single invoice against all rules.
        
        Args:
            invoice: Invoice to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        invoice_id = invoice.invoice_number or invoice.source_file or "UNKNOWN"
        result = ValidationResult(invoice_id=invoice_id, is_valid=True)
        
        # COMPLETENESS RULES
        self._validate_completeness(invoice, result)
        
        # TYPE/FORMAT RULES
        self._validate_formats(invoice, result)
        
        # BUSINESS RULES
        self._validate_business_rules(invoice, result)
        
        # ANOMALY RULES
        self._validate_anomalies(invoice, result)
        
        return result
    
    # ===== COMPLETENESS RULES =====
    
    def _validate_completeness(self, invoice: Invoice, result: ValidationResult):
        """Validate that required fields are present and non-empty"""
        
        # Rule 1: Invoice number required
        if not invoice.invoice_number or not invoice.invoice_number.strip():
            result.add_error(
                rule="invoice_number_required",
                field="invoice_number",
                message="Invoice number is required and cannot be empty"
            )
        
        # Rule 2: Invoice date required
        if not invoice.invoice_date:
            result.add_error(
                rule="invoice_date_required",
                field="invoice_date",
                message="Invoice date is required"
            )
        
        # Rule 3: Parties required (seller and buyer names)
        if not invoice.seller_name or not invoice.seller_name.strip():
            result.add_error(
                rule="seller_name_required",
                field="seller_name",
                message="Seller name is required and cannot be empty"
            )
        
        if not invoice.buyer_name or not invoice.buyer_name.strip():
            result.add_error(
                rule="buyer_name_required",
                field="buyer_name",
                message="Buyer name is required and cannot be empty"
            )
        
        # Rule 4: Key amounts required
        if invoice.gross_total is None:
            result.add_error(
                rule="gross_total_required",
                field="gross_total",
                message="Gross total (final amount) is required"
            )
    
    # ===== FORMAT/TYPE RULES =====
    
    def _validate_formats(self, invoice: Invoice, result: ValidationResult):
        """Validate data types and formats"""
        
        # Rule: Currency must be valid
        if invoice.currency and invoice.currency not in [c.value for c in Currency]:
            result.add_error(
                rule="invalid_currency",
                field="currency",
                message=f"Currency '{invoice.currency}' is not in known set (EUR, USD, INR, GBP)"
            )
        
        # Rule: Dates must be reasonable (not too far in past/future)
        if invoice.invoice_date:
            if not self._is_reasonable_date(invoice.invoice_date):
                result.add_warning(
                    rule="unreasonable_invoice_date",
                    field="invoice_date",
                    message=f"Invoice date {invoice.invoice_date} seems unreasonable (too far in past/future)"
                )
        
        if invoice.due_date:
            if not self._is_reasonable_date(invoice.due_date):
                result.add_warning(
                    rule="unreasonable_due_date",
                    field="due_date",
                    message=f"Due date {invoice.due_date} seems unreasonable (too far in past/future)"
                )
    
    # ===== BUSINESS RULES =====
    
    def _validate_business_rules(self, invoice: Invoice, result: ValidationResult):
        """Validate business logic rules"""
        
        # Rule 5: Due date must be on or after invoice date
        if invoice.invoice_date and invoice.due_date:
            if invoice.due_date < invoice.invoice_date:
                result.add_error(
                    rule="invalid_date_order",
                    field="due_date",
                    message=f"Due date ({invoice.due_date}) cannot be before invoice date ({invoice.invoice_date})"
                )
        
        # Rule 6: Totals consistency (net + tax ≈ gross)
        if invoice.net_total is not None and invoice.tax_amount is not None and invoice.gross_total is not None:
            expected_gross = invoice.net_total + invoice.tax_amount
            if not self._amounts_match(expected_gross, invoice.gross_total):
                result.add_error(
                    rule="totals_mismatch",
                    field="gross_total",
                    message=f"Net total ({invoice.net_total}) + Tax ({invoice.tax_amount}) "
                           f"= {expected_gross} does not match Gross total ({invoice.gross_total})"
                )
        
        # Rule 7: Line items sum should match net total
        if invoice.line_items and invoice.net_total is not None:
            line_items_sum = sum(
                (item.line_total for item in invoice.line_items if item.line_total),
                start=Decimal(0)
            )
            
            if line_items_sum > 0 and not self._amounts_match(line_items_sum, invoice.net_total):
                result.add_warning(
                    rule="line_items_sum_mismatch",
                    field="line_items",
                    message=f"Sum of line items ({line_items_sum}) does not match net total ({invoice.net_total})"
                )
        
        # Rule 8: Non-negative amounts
        if invoice.net_total is not None and invoice.net_total < 0:
            result.add_error(
                rule="negative_amount",
                field="net_total",
                message="Net total cannot be negative"
            )
        
        if invoice.tax_amount is not None and invoice.tax_amount < 0:
            result.add_error(
                rule="negative_amount",
                field="tax_amount",
                message="Tax amount cannot be negative"
            )
        
        if invoice.gross_total is not None and invoice.gross_total < 0:
            result.add_error(
                rule="negative_amount",
                field="gross_total",
                message="Gross total cannot be negative"
            )
    
    # ===== ANOMALY RULES =====
    
    def _validate_anomalies(self, invoice: Invoice, result: ValidationResult):
        """Validate for anomalies and duplicates"""
        
        # Rule 9: Duplicate detection
        if invoice.invoice_number and invoice.seller_name:
            invoice_key = (
                invoice.invoice_number.strip().upper(),
                invoice.seller_name.strip().upper(),
                str(invoice.invoice_date)
            )
            
            if invoice_key in self.seen_invoices:
                result.add_error(
                    rule="duplicate_invoice",
                    field="invoice_number",
                    message=f"Duplicate invoice detected: {invoice.invoice_number} from {invoice.seller_name}"
                )
            else:
                self.seen_invoices.add(invoice_key)
        
        # Rule 10: Reasonable date range check (already in format validation)
        # This is covered in _validate_formats
        
        # Rule 11: Currency check (already in format validation)
        # This is covered in _validate_formats
    
    # ===== HELPER METHODS =====
    
    def _amounts_match(self, amount1: Decimal, amount2: Decimal) -> bool:
        """
        Check if two amounts match within tolerance.
        Allows for small rounding differences.
        """
        if amount1 == 0 and amount2 == 0:
            return True
        
        if amount1 == 0 or amount2 == 0:
            return abs(amount1 - amount2) < Decimal('0.01')
        
        difference = abs(amount1 - amount2)
        avg = (abs(amount1) + abs(amount2)) / 2
        
        return difference / avg <= Decimal(str(self.tolerance))
    
    def _is_reasonable_date(self, check_date: date) -> bool:
        """Check if date is within reasonable range (10 years past to 2 years future)"""
        today = date.today()
        min_date = today - timedelta(days=365 * 10)  # 10 years ago
        max_date = today + timedelta(days=365 * 2)   # 2 years in future
        
        return min_date <= check_date <= max_date
    
    def _create_summary(self, results: List[ValidationResult]) -> ValidationSummary:
        """Create summary statistics from validation results"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid
        with_warnings = sum(1 for r in results if r.warnings)
        
        error_counts = {}
        warning_counts = {}
        
        for result in results:
            for error in result.errors:
                key = f"{error.rule}: {error.field}" if error.field else error.rule
                error_counts[key] = error_counts.get(key, 0) + 1
            
            for warning in result.warnings:
                key = f"{warning.rule}: {warning.field}" if warning.field else warning.rule
                warning_counts[key] = warning_counts.get(key, 0) + 1
        
        return ValidationSummary(
            total_invoices=total,
            valid_invoices=valid,
            invalid_invoices=invalid,
            invoices_with_warnings=with_warnings,
            error_counts=error_counts,
            warning_counts=warning_counts
        )