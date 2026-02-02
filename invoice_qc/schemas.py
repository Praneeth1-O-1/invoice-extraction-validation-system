"""
Invoice data models and schemas using Pydantic.
These define the structure of extracted invoice data.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Currency(str, Enum):
    """Supported currencies"""
    EUR = "EUR"
    USD = "USD"
    INR = "INR"
    GBP = "GBP"


class LineItem(BaseModel):
    """Individual line item in an invoice"""
    description: Optional[str] = Field(None, description="Product/service description")
    quantity: Optional[float] = Field(None, description="Quantity ordered", ge=0)
    unit_price: Optional[Decimal] = Field(None, description="Price per unit")
    line_total: Optional[Decimal] = Field(None, description="Total for this line item")
    tax_rate: Optional[float] = Field(None, description="Tax rate percentage", ge=0, le=100)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class Invoice(BaseModel):
    """
    Complete invoice schema with all extracted fields.
    
    Core fields (10+ invoice-level fields):
    1. invoice_number - Unique identifier
    2. invoice_date - Date invoice was issued
    3. due_date - Payment due date
    4. seller_name - Name of the selling party
    5. seller_address - Address of seller
    6. seller_tax_id - Tax/VAT ID of seller
    7. buyer_name - Name of the buying party
    8. buyer_address - Address of buyer
    9. buyer_tax_id - Tax/VAT ID of buyer
    10. currency - Currency code (EUR, USD, etc.)
    11. net_total - Subtotal before tax
    12. tax_amount - Total tax amount
    13. gross_total - Final total including tax
    14. payment_terms - Payment terms/conditions
    """
    
    # Identifiers
    invoice_number: Optional[str] = Field(None, description="Invoice number/ID")
    external_reference: Optional[str] = Field(None, description="External reference or PO number")
    
    # Seller information
    seller_name: Optional[str] = Field(None, description="Seller/vendor company name")
    seller_address: Optional[str] = Field(None, description="Seller full address")
    seller_tax_id: Optional[str] = Field(None, description="Seller VAT/Tax ID")
    
    # Buyer information
    buyer_name: Optional[str] = Field(None, description="Buyer/customer company name")
    buyer_address: Optional[str] = Field(None, description="Buyer full address")
    buyer_tax_id: Optional[str] = Field(None, description="Buyer VAT/Tax ID")
    
    # Dates
    invoice_date: Optional[date] = Field(None, description="Invoice issue date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    
    # Financial information
    currency: Optional[Currency] = Field(None, description="Currency code")
    net_total: Optional[Decimal] = Field(None, description="Subtotal before tax", ge=0)
    tax_amount: Optional[Decimal] = Field(None, description="Total tax amount", ge=0)
    tax_rate: Optional[float] = Field(None, description="Tax rate percentage", ge=0, le=100)
    gross_total: Optional[Decimal] = Field(None, description="Total including tax", ge=0)
    
    # Additional information
    payment_terms: Optional[str] = Field(None, description="Payment terms (e.g., Net 30)")
    
    # Line items
    line_items: Optional[List[LineItem]] = Field(default_factory=list, description="Invoice line items")
    
    # Metadata
    source_file: Optional[str] = Field(None, description="Source PDF filename")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat() if v else None
        }
    
    @field_validator('invoice_date', 'due_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date from various formats"""
        if v is None or isinstance(v, date):
            return v
        if isinstance(v, str):
            # Clean string
            v = v.strip()
            # Try common date formats (English & International)
            formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%Y',
                '%d-%m-%Y', '%B %d, %Y', '%d %b %Y'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        return v


class ValidationError(BaseModel):
    """Single validation error"""
    rule: str = Field(..., description="Rule that failed (e.g., 'missing_field')")
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Human-readable error message")
    severity: str = Field(default="error", description="error, warning, or info")


class ValidationResult(BaseModel):
    """Validation result for a single invoice"""
    invoice_id: str = Field(..., description="Invoice identifier")
    is_valid: bool = Field(..., description="Whether invoice passed all validations")
    errors: List[ValidationError] = Field(default_factory=list, description="List of validation errors")
    warnings: List[ValidationError] = Field(default_factory=list, description="List of warnings")
    
    def add_error(self, rule: str, message: str, field: Optional[str] = None):
        """Add an error to the result"""
        self.errors.append(ValidationError(rule=rule, field=field, message=message, severity="error"))
        self.is_valid = False
    
    def add_warning(self, rule: str, message: str, field: Optional[str] = None):
        """Add a warning to the result"""
        self.warnings.append(ValidationError(rule=rule, field=field, message=message, severity="warning"))


class ValidationSummary(BaseModel):
    """Summary of validation results across all invoices"""
    total_invoices: int = Field(..., description="Total number of invoices validated")
    valid_invoices: int = Field(..., description="Number of valid invoices")
    invalid_invoices: int = Field(..., description="Number of invalid invoices")
    invoices_with_warnings: int = Field(default=0, description="Number of invoices with warnings")
    error_counts: dict[str, int] = Field(default_factory=dict, description="Count of each error type")
    warning_counts: dict[str, int] = Field(default_factory=dict, description="Count of each warning type")


class ValidationReport(BaseModel):
    """Complete validation report"""
    summary: ValidationSummary
    results: List[ValidationResult]
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }