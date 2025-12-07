"""
FastAPI application for Invoice QC Service.
Provides HTTP API endpoints for validation and extraction.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path to import invoice_qc
sys.path.append(str(Path(__file__).parent.parent))

from invoice_qc.schemas import Invoice, ValidationReport
from invoice_qc.validator import InvoiceValidator
from invoice_qc.extractor import InvoiceExtractor

# Create FastAPI app
app = FastAPI(
    title="Invoice QC Service API",
    description="API for extracting and validating invoice data",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
validator = InvoiceValidator()
extractor = InvoiceExtractor()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Invoice QC Service API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "validate": "/validate-json",
            "extract_and_validate": "/extract-and-validate-pdfs"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status information about the service
    """
    return {
        "status": "ok",
        "service": "invoice-qc-service",
        "version": "1.0.0"
    }


@app.post("/validate-json", response_model=ValidationReport)
async def validate_invoices(invoices: List[Invoice]):
    """
    Validate a list of invoices provided as JSON.
    
    Args:
        invoices: List of invoice objects to validate
        
    Returns:
        ValidationReport with summary and per-invoice results
        
    Example:
        ```bash
        curl -X POST http://localhost:8000/validate-json \\
          -H "Content-Type: application/json" \\
          -d '[{"invoice_number": "INV-001", "invoice_date": "2024-01-10", ...}]'
        ```
    """
    try:
        if not invoices:
            raise HTTPException(status_code=400, detail="No invoices provided")
        
        # Validate invoices
        report = validator.validate_batch(invoices)
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@app.post("/extract-and-validate-pdfs")
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    """
    Extract data from uploaded PDFs and validate them.
    
    Args:
        files: List of PDF files to process
        
    Returns:
        Dictionary containing extracted invoices and validation report
        
    Example:
        ```bash
        curl -X POST http://localhost:8000/extract-and-validate-pdfs \\
          -F "files=@invoice1.pdf" \\
          -F "files=@invoice2.pdf"
        ```
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Check all files are PDFs
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not a PDF"
                )
        
        # Create temporary directory for PDFs
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded files
            saved_files = []
            for file in files:
                file_path = temp_path / file.filename
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(file.file, f)
                saved_files.append(file_path)
            
            # Extract invoices
            invoices = extractor.extract_from_directory(temp_path)
            
            if not invoices:
                return {
                    "extracted_invoices": [],
                    "validation_report": None,
                    "message": "No invoices could be extracted from the provided PDFs"
                }
            
            # Validate invoices
            report = validator.validate_batch(invoices)
            
            return {
                "extracted_invoices": [invoice.model_dump(mode='json') for invoice in invoices],
                "validation_report": report.model_dump(mode='json'),
                "files_processed": len(files),
                "invoices_extracted": len(invoices)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDFs: {str(e)}"
        )


@app.get("/api/info")
async def api_info():
    """Get information about available validation rules"""
    return {
        "validation_rules": {
            "completeness": [
                {
                    "rule": "invoice_number_required",
                    "description": "Invoice must have a non-empty invoice number"
                },
                {
                    "rule": "invoice_date_required",
                    "description": "Invoice must have an invoice date"
                },
                {
                    "rule": "parties_required",
                    "description": "Seller and buyer names must not be empty"
                },
                {
                    "rule": "amounts_required",
                    "description": "Key financial amounts must be present"
                }
            ],
            "business_rules": [
                {
                    "rule": "date_order",
                    "description": "Due date must be on or after invoice date"
                },
                {
                    "rule": "totals_consistency",
                    "description": "Net total + tax amount should equal gross total"
                },
                {
                    "rule": "line_items_sum",
                    "description": "Sum of line item totals should match net total"
                },
                {
                    "rule": "non_negative_amounts",
                    "description": "All amounts must be non-negative"
                }
            ],
            "anomaly_rules": [
                {
                    "rule": "duplicate_invoice",
                    "description": "No duplicate invoices (same invoice number + seller)"
                },
                {
                    "rule": "reasonable_date_range",
                    "description": "Dates should be within reasonable range"
                },
                {
                    "rule": "valid_currency",
                    "description": "Currency must be from known set (EUR, USD, INR, GBP)"
                }
            ]
        },
        "schema_fields": {
            "identifiers": ["invoice_number", "external_reference"],
            "seller": ["seller_name", "seller_address", "seller_tax_id"],
            "buyer": ["buyer_name", "buyer_address", "buyer_tax_id"],
            "dates": ["invoice_date", "due_date"],
            "financial": ["currency", "net_total", "tax_amount", "tax_rate", "gross_total"],
            "additional": ["payment_terms", "line_items"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)