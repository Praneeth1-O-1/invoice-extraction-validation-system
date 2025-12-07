"""
Simple script to test the Invoice QC Service API.
Run this after starting the API server with: uvicorn api.main:app --reload
"""

import requests
import json
from pathlib import Path
from datetime import date

# API base URL
BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_validate_json():
    """Test the JSON validation endpoint"""
    print("\n=== Testing JSON Validation ===")
    
    # Sample invoice data
    sample_invoices = [
        {
            "invoice_number": "INV-001",
            "invoice_date": "2024-01-10",
            "due_date": "2024-01-25",
            "seller_name": "ACME Corporation GmbH",
            "seller_address": "123 Business St, Berlin",
            "buyer_name": "Example Industries Inc",
            "buyer_address": "456 Commerce Ave, Munich",
            "currency": "EUR",
            "net_total": 1000.00,
            "tax_amount": 190.00,
            "gross_total": 1190.00,
            "payment_terms": "Net 30"
        },
        {
            "invoice_number": "INV-002",
            "invoice_date": "2024-01-15",
            "due_date": "2024-01-10",  # Invalid: due before invoice date!
            "seller_name": "Tech Solutions Ltd",
            "buyer_name": "Client Corp",
            "currency": "USD",
            "net_total": 500.00,
            "tax_amount": 50.00,
            "gross_total": 600.00  # Invalid: doesn't match net + tax!
        },
        {
            "invoice_number": "INV-003",
            # Missing invoice_date - should fail validation
            "seller_name": "Services Inc",
            "buyer_name": "Customer LLC",
            "gross_total": 250.00
        }
    ]
    
    response = requests.post(
        f"{BASE_URL}/validate-json",
        json=sample_invoices,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n--- Validation Summary ---")
        print(f"Total Invoices: {result['summary']['total_invoices']}")
        print(f"Valid Invoices: {result['summary']['valid_invoices']}")
        print(f"Invalid Invoices: {result['summary']['invalid_invoices']}")
        
        if result['summary']['error_counts']:
            print(f"\n--- Error Counts ---")
            for error, count in result['summary']['error_counts'].items():
                print(f"  {error}: {count}")
        
        print(f"\n--- Per-Invoice Results ---")
        for invoice_result in result['results']:
            status = "✓ VALID" if invoice_result['is_valid'] else "✗ INVALID"
            print(f"\n{invoice_result['invoice_id']}: {status}")
            if invoice_result['errors']:
                for error in invoice_result['errors']:
                    print(f"  - {error['message']}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_extract_and_validate_pdfs():
    """Test the PDF upload and validation endpoint"""
    print("\n=== Testing PDF Extraction & Validation ===")
    
    pdf_dir = Path("pdfs")
    
    if not pdf_dir.exists():
        print("Warning: pdfs/ directory not found. Skipping PDF test.")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("Warning: No PDF files found in pdfs/ directory. Skipping PDF test.")
        return False
    
    # Take first 2 PDFs for testing
    test_files = pdf_files[:2]
    
    print(f"Uploading {len(test_files)} PDF files...")
    
    files = [
        ('files', (pdf.name, open(pdf, 'rb'), 'application/pdf'))
        for pdf in test_files
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/extract-and-validate-pdfs",
            files=files
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nFiles Processed: {result['files_processed']}")
            print(f"Invoices Extracted: {result['invoices_extracted']}")
            
            if result.get('validation_report'):
                summary = result['validation_report']['summary']
                print(f"\n--- Validation Summary ---")
                print(f"Valid: {summary['valid_invoices']}/{summary['total_invoices']}")
                
                if summary['error_counts']:
                    print(f"\nTop Errors:")
                    for error, count in list(summary['error_counts'].items())[:3]:
                        print(f"  - {error}: {count}")
        else:
            print(f"Error: {response.text}")
        
        return response.status_code == 200
    
    finally:
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()


def test_api_info():
    """Test the API info endpoint"""
    print("\n=== Testing API Info ===")
    response = requests.get(f"{BASE_URL}/api/info")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        info = response.json()
        print(f"\nValidation Rules Available:")
        print(f"  Completeness: {len(info['validation_rules']['completeness'])}")
        print(f"  Business: {len(info['validation_rules']['business_rules'])}")
        print(f"  Anomaly: {len(info['validation_rules']['anomaly_rules'])}")
    
    return response.status_code == 200


def main():
    """Run all API tests"""
    print("=" * 60)
    print("Invoice QC Service - API Test Suite")
    print("=" * 60)
    print("\nMake sure the API is running:")
    print("  uvicorn api.main:app --reload")
    print("=" * 60)
    
    results = {
        "Health Check": test_health_check(),
        "JSON Validation": test_validate_json(),
        "API Info": test_api_info(),
        "PDF Upload": test_extract_and_validate_pdfs(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server.")
        print("Please start the server with: uvicorn api.main:app --reload")
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")