# invoice_qc/__init__.py
"""
Invoice QC Service - Invoice Extraction and Quality Control System
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from invoice_qc.schemas import (
    Invoice,
    LineItem,
    ValidationReport,
    ValidationResult,
    ValidationSummary,
)

from invoice_qc.extractor import InvoiceExtractor
from invoice_qc.validator import InvoiceValidator

__all__ = [
    "Invoice",
    "LineItem",
    "ValidationReport",
    "ValidationResult",
    "ValidationSummary",
    "InvoiceExtractor",
    "InvoiceValidator",
]


# api/__init__.py
"""
FastAPI application for Invoice QC Service
"""

__version__ = "1.0.0"