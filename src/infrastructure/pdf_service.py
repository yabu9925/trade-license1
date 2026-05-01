from fpdf import FPDF
from src.domain.trade_license.aggregate import TradeLicenseApplication
import os

class PDFService:
    def generate_license_pdf(self, app: TradeLicenseApplication) -> bytes:
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # --- BACKGROUND & BORDER ---
        pdf.set_line_width(1)
        pdf.rect(5, 5, 200, 287) # Outer border
        pdf.set_line_width(0.2)
        pdf.rect(7, 7, 196, 283) # Inner border
        
        # --- HEADER ---
        pdf.set_fill_color(0, 51, 102) # Dark Blue
        pdf.rect(7, 7, 196, 40, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 26)
        pdf.set_y(15)
        pdf.cell(0, 15, "CERTIFICATE OF TRADE LICENSE", ln=True, align="C")
        pdf.set_font("Helvetica", "I", 12)
        pdf.cell(0, 10, "GOVERNMENT OF TRADE PORTAL - OFFICIAL DOCUMENT", ln=True, align="C")
        
        # Reset text color
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(55)
        
        # --- APPLICANT PHOTO ---
        photo_path = None
        for doc in app.attachments:
            if doc.file_name == "Applicant Photo":
                photo_path = doc.storage_uri
                break
        
        if photo_path and os.path.exists(photo_path):
            # Place photo in top right
            pdf.image(photo_path, x=150, y=55, w=40, h=50)
            pdf.rect(150, 55, 40, 50) # Photo frame
        
        # --- LICENSE DETAILS ---
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_x(15)
        pdf.cell(0, 10, f"LICENSE NUMBER: {app.id[-12:].upper()}", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "", 12)
        
        def add_field(label, value):
            pdf.set_x(15)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(50, 8, f"{label}:", 0)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, str(value), 0, 1)

        add_field("ENTITY NAME", app.business_details.name)
        add_field("BUSINESS TYPE", app.business_details.type)
        add_field("LOCATION", app.business_details.address)
        add_field("HOLDER ID", app.applicant_id)
        add_field("STATUS", "AUTHORIZED & ACTIVE")
        add_field("ISSUE DATE", "MAY 01, 2026")
        
        pdf.ln(10)
        
        # --- ACTIVITY DESCRIPTION ---
        pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 10, "AUTHORIZED BUSINESS ACTIVITIES:", ln=True)
        pdf.set_x(15)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(130, 6, app.business_details.activity_description)
        
        # --- FOOTER & STAMP ---
        stamp_path = "frontend/stamp.png"
        if os.path.exists(stamp_path):
            pdf.image(stamp_path, x=140, y=190, w=50)
        
        # Signature Line
        pdf.set_y(240)
        pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(80, 10, "__________________________", ln=True, align="L")
        pdf.set_x(15)
        pdf.cell(80, 5, "DIRECTOR OF LICENSING", ln=True, align="L")
        
        # Final Verification Note
        pdf.set_y(270)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 10, "This license is valid for 12 months from the date of issue.", ln=True, align="C")
        
        return pdf.output()
