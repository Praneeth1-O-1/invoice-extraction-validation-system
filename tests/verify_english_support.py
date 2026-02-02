from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import requests
import json
import os

def create_invoice_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(400, 750, "INVOICE")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 750, "Bioplex")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "we love chemistry")
    
    # Invoice Details
    c.drawString(400, 730, "INVOICE # BPXINV-00550")
    c.drawString(400, 715, "DATE: 23.05.2021")
    
    # Seller Address (implied under Bioplex)
    c.drawString(50, 700, "5 Rue Bader")
    c.drawString(50, 685, "Narbonne, Aude, 11100")
    
    # Bill To
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 650, "TO:")
    c.setFont("Helvetica", 10)
    c.drawString(50, 635, "Roger Bigot")
    c.drawString(50, 620, "bonbono")
    c.drawString(50, 605, "4 Rue des Cites")
    
    # Line Items Table Header
    y = 550
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "QUANTITY")
    c.drawString(150, y, "DESCRIPTION")
    c.drawString(400, y, "UNIT PRICE")
    c.drawString(500, y, "TOTAL")
    
    # Line Item 1
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "10")
    c.drawString(150, y, "Dextromethorphan polistirex")
    c.drawString(400, y, "12.45")
    c.drawString(500, y, "124.50")
    
    # Line Item 2
    y -= 20
    c.drawString(50, y, "25")
    c.drawString(150, y, "Venlafaxine Hydrochloride")
    c.drawString(400, y, "16.00")
    c.drawString(500, y, "400.00")
    
    # Totals
    y -= 100
    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, y, "SUBTOTAL")
    c.drawString(500, y, "524.50")
    
    y -= 20
    c.drawString(400, y, "SALES TAX")
    c.drawString(500, y, "52.45") # 10% tax example_lines
    
    y -= 20
    c.drawString(400, y, "TOTAL DUE")
    c.drawString(500, y, "576.95")
    
    c.save()
    print(f"Created {filename}")

def test_api(filename):
    url = "http://localhost:8000/extract-and-validate-pdfs"
    files = {'files': open(filename, 'rb')}
    
    try:
        response = requests.post(url, files=files)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))
        
        # Verify extraction
        invoices = data.get("extracted_invoices", [])
        if not invoices:
            print("FAILED: No invoices extracted")
            return
            
        inv = invoices[0]
        if inv["invoice_number"] != "BPXINV-00550":
            print(f"FAILED: Number mismatch {inv['invoice_number']}")
        elif inv["gross_total"] != 576.95:
             # Float comparison might be tricky, but exact match for 2 decimal default string?
             print(f"FAILED: Total mismatch {inv['gross_total']}")
        else:
            print("SUCCESS: Extraction verified!")
            
    except Exception as e:
        print(f"FAILED: API request error {str(e)}")

if __name__ == "__main__":
    pdf_name = "test_english_invoice.pdf"
    create_invoice_pdf(pdf_name)
    test_api(pdf_name)
    # Cleanup
    # if os.path.exists(pdf_name):
    #     os.remove(pdf_name)

    import pdfplumber
    with pdfplumber.open(pdf_name) as pdf:
        print("\n--- PDF LAYOUT TEXT ---")
        print(pdf.pages[0].extract_text(layout=True))
        print("--- END PDF LAYOUT TEXT ---\n")
