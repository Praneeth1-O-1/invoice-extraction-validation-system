from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import requests
import json
import os

def create_invoice_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    # Create a layout that closely mimics the failure case
    # "TO:" and "SHIP TO:" in columns
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 750, "Bioplex")
    
    # 2-column layout for TO and SHIP TO
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 650, "TO:")
    c.drawString(300, 650, "SHIP TO:")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, 635, "Roger Bigot")
    c.drawString(300, 635, "Roger Bigot")
    
    c.drawString(50, 620, "bonbono")
    c.drawString(300, 620, "bonbono")
    
    c.drawString(50, 605, "4 Rue des Cites")
    c.drawString(300, 605, "4 Rue des Cites")
    
    c.save()

def test_api(filename):
    url = "http://localhost:8000/extract-and-validate-pdfs"
    files = {'files': open(filename, 'rb')}
    try:
        requests.post(url, files=files)
    except:
        pass

if __name__ == "__main__":
    pdf_name = "debug_invoice.pdf"
    create_invoice_pdf(pdf_name)
    test_api(pdf_name)
    if os.path.exists(pdf_name):
        os.remove(pdf_name)
