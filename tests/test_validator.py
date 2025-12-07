"""
Unit tests for invoice validator
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from invoice_qc.schemas import Invoice, LineItem
from invoice_qc.validator import InvoiceValidator


def test_valid_invoice():
    """Test that a completely valid invoice passes all checks"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        due_date=date(2024, 1, 25),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        currency="EUR",
        net_total=Decimal("100.00"),
        tax_amount=Decimal("19.00"),
        gross_total=Decimal("119.00")
    )
    
    result = validator.validate_invoice(invoice)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_missing_invoice_number():
    """Test that missing invoice number is caught"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_date=date(2024, 1, 10),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        gross_total=Decimal("119.00")
    )
    
    result = validator.validate_invoice(invoice)
    assert result.is_valid is False
    assert any(e.rule == "invoice_number_required" for e in result.errors)


def test_missing_parties():
    """Test that missing seller/buyer names are caught"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        gross_total=Decimal("119.00")
    )
    
    result = validator.validate_invoice(invoice)
    assert result.is_valid is False
    assert any(e.rule == "seller_name_required" for e in result.errors)
    assert any(e.rule == "buyer_name_required" for e in result.errors)


def test_invalid_date_order():
    """Test that due date before invoice date is caught"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 25),
        due_date=date(2024, 1, 10),  # Before invoice date!
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        gross_total=Decimal("119.00")
    )
    
    result = validator.validate_invoice(invoice)
    assert result.is_valid is False
    assert any(e.rule == "invalid_date_order" for e in result.errors)


def test_totals_mismatch():
    """Test that incorrect totals are caught"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        currency="EUR",
        net_total=Decimal("100.00"),
        tax_amount=Decimal("19.00"),
        gross_total=Decimal("125.00")  # Wrong! Should be 119.00
    )
    
    result = validator.validate_invoice(invoice)
    assert result.is_valid is False
    assert any(e.rule == "totals_mismatch" for e in result.errors)


def test_negative_amounts():
    """Test that negative amounts are caught"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        net_total=Decimal("-100.00"),  # Negative!
        gross_total=Decimal("-100.00")
    )
    
    result = validator.validate_invoice(invoice)
    assert result.is_valid is False
    assert any(e.rule == "negative_amount" for e in result.errors)


def test_duplicate_invoice():
    """Test that duplicate invoices are detected"""
    validator = InvoiceValidator()
    
    invoice1 = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        gross_total=Decimal("119.00")
    )
    
    invoice2 = Invoice(
        invoice_number="INV-001",  # Same number
        invoice_date=date(2024, 1, 10),  # Same date
        seller_name="ACME Corp",  # Same seller
        buyer_name="Different Inc",
        gross_total=Decimal("200.00")
    )
    
    # Validate batch
    report = validator.validate_batch([invoice1, invoice2])
    
    # Second invoice should have duplicate error
    assert any(
        any(e.rule == "duplicate_invoice" for e in r.errors)
        for r in report.results
    )


def test_line_items_sum():
    """Test that line items sum validation works"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        currency="EUR",
        net_total=Decimal("100.00"),
        line_items=[
            LineItem(description="Item 1", quantity=2, unit_price=Decimal("25.00"), line_total=Decimal("50.00")),
            LineItem(description="Item 2", quantity=1, unit_price=Decimal("30.00"), line_total=Decimal("30.00")),
            # Sum = 80.00, but net_total = 100.00 → mismatch!
        ]
    )
    
    result = validator.validate_invoice(invoice)
    # Should have a warning (not error) about line items sum
    assert any(w.rule == "line_items_sum_mismatch" for w in result.warnings)


def test_invalid_currency():
    """Test that invalid currency codes are caught"""
    validator = InvoiceValidator()
    
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        currency="XXX",  # Invalid currency
        gross_total=Decimal("119.00")
    )
    
    result = validator.validate_invoice(invoice)
    assert result.is_valid is False
    assert any(e.rule == "invalid_currency" for e in result.errors)


def test_validation_summary():
    """Test that validation summary is calculated correctly"""
    validator = InvoiceValidator()
    
    invoices = [
        Invoice(invoice_number="INV-001", invoice_date=date(2024, 1, 10), 
                seller_name="A", buyer_name="B", gross_total=Decimal("100")),
        Invoice(invoice_number="INV-002", invoice_date=date(2024, 1, 11), 
                seller_name="A", buyer_name="B", gross_total=Decimal("200")),
        Invoice(invoice_number="INV-003", seller_name="A", buyer_name="B"),  # Missing date - invalid
    ]
    
    report = validator.validate_batch(invoices)
    
    assert report.summary.total_invoices == 3
    assert report.summary.valid_invoices == 2
    assert report.summary.invalid_invoices == 1
    assert "invoice_date_required" in str(report.summary.error_counts)


def test_tolerance_matching():
    """Test that amount tolerance works correctly"""
    validator = InvoiceValidator(tolerance=0.02)  # 2% tolerance
    
    # 100 + 19 = 119, but due to rounding might be 119.01
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2024, 1, 10),
        seller_name="ACME Corp",
        buyer_name="Example Inc",
        net_total=Decimal("100.00"),
        tax_amount=Decimal("19.00"),
        gross_total=Decimal("119.01")  # Within 2% tolerance
    )
    
    result = validator.validate_invoice(invoice)
    # Should pass because difference is within tolerance
    assert not any(e.rule == "totals_mismatch" for e in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])