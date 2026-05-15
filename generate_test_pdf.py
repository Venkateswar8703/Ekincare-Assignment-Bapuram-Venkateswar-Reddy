"""
Generate a multi-page test PDF from sample medical claim content.
Uses PyMuPDF (fitz) to create pages with realistic document text.
"""

import fitz  # PyMuPDF
import os

PAGES = [
    # Page 1: Claim Form
    """MEDICAL CLAIM FORM
HealthCare Insurance Company

Claim Reference: CLM-2024-789456
Date Filed: January 15, 2025

PATIENT INFORMATION

Patient Name: John Michael Smith
Date of Birth: March 15, 1985
Policy Number: POL-987654321
Contact Number: +1-555-0123
Email: john.smith@email.com

CLAIM DETAILS

Type of Service: Outpatient Consultation
Date of Service: January 10, 2025
Provider Name: Dr. Sarah Johnson, MD
Hospital/Clinic: City Medical Center
Diagnosis: Acute Bronchitis (ICD-10: J20.9)
Treatment Provided: Consultation, Chest X-Ray, Prescription
Total Amount Claimed: $450.00
Insurance Coverage: 80%
Patient Responsibility: $90.00

DECLARATION
I hereby declare that the information provided above is true
and accurate to the best of my knowledge.

Signature: ___________________
Date: ___________________""",

    # Page 2: Cheque / Bank Details
    """GLOBAL TRUST BANK
123 Financial District
New York, NY 10004

CHEQUE DETAILS

Cheque Number: CH-456789123
Account Number: XXXX-XXXX-1234
Date Issued: February 1, 2025

Payee: John Michael Smith
Amount: $1,500.00

BANK ACCOUNT DETAILS

Account Holder Name: John Michael Smith
Account Type: Savings Account
Bank Name: Global Trust Bank
Branch: Main Branch - New York
IFSC/Routing Number: GTB000123456
SWIFT Code: GTBNUS33XXX
Account Number: 1234567890123
Account Status: Active

This is a computer-generated document.
For verification, contact Global Trust Bank at 1-800-BANK-GTB""",

    # Page 3: Identity Document
    """GOVERNMENT ID CARD

[PHOTO]                    Signature: J.M. Smith

PERSONAL INFORMATION

Full Name: JOHN MICHAEL SMITH
ID Number: ID-987-654-321
Date of Birth: 15-MAR-1985
Gender: Male
Blood Group: O+
Address: 456 Oak Street, Apt 12B
         Springfield, IL 62701

Issue Date: 15-JAN-2023
Expiry Date: 15-JAN-2033

|||| |||| |||| |||| ||||

This document contains security features.
Issued by Department of Motor Vehicles.""",

    # Page 4: Discharge Summary
    """CITY MEDICAL CENTER
789 Healthcare Boulevard, Boston, MA 02101
Tel: (555) 987-6543

DISCHARGE SUMMARY

PATIENT INFORMATION
Name: John Michael Smith
MRN: MRN-123456789
Date of Birth: March 15, 1985 (Age: 40)
Admission Date: January 20, 2025
Discharge Date: January 25, 2025
Length of Stay: 5 days
Attending Physician: Dr. Sarah Johnson, MD

CLINICAL SUMMARY

Admission Diagnosis: Community Acquired Pneumonia (CAP)

Hospital Course:
Patient admitted with fever, cough, and shortness of breath.
Chest X-ray confirmed right lower lobe pneumonia. Started on
IV antibiotics (Ceftriaxone 1g daily). Patient showed gradual
improvement with resolution of fever by day 3. Oxygen
saturation improved to 96% on room air.

DISCHARGE INFORMATION
Condition at Discharge: Stable, improved
Discharge Medications:
  - Amoxicillin 500mg TID x 7 days
  - Acetaminophen 500mg PRN for pain
Follow-up: Outpatient clinic in 1 week
Activity: Gradual return to normal activities
Diet: Regular diet, increase fluid intake

Digitally signed by: Dr. Sarah Johnson, MD
Date: January 25, 2025, 4:30 PM""",

    # Page 5: Prescription
    """Rx  Dr. Sarah Johnson, MD
    Internal Medicine Specialist
    City Medical Center, Suite 304
    Boston, MA 02101
    License: MD-987654 | Phone: (555) 123-4567

PATIENT INFORMATION
Name: John Michael Smith       Age: 40 years
Date: February 1, 2025         Patient ID: PAT-789456

PRESCRIPTION

1. Amoxicillin 500mg
   Dosage: 1 capsule three times daily
   Duration: 7 days
   Instructions: Take with food

2. Acetaminophen 500mg
   Dosage: 1-2 tablets every 6 hours as needed
   Duration: As required
   Instructions: Do not exceed 8 tablets in 24 hours

3. Cetirizine 10mg
   Dosage: 1 tablet once daily at bedtime
   Duration: 5 days
   Instructions: May cause drowsiness

GENERAL INSTRUCTIONS:
- Complete the full course of antibiotics
- Drink plenty of fluids (8-10 glasses of water daily)
- Rest adequately
- Follow up if symptoms worsen

Doctor's Signature: ___________________
Date: Feb 1, 2025
This prescription is valid for 30 days from the date of issue.""",

    # Page 6: Investigation Report (CBC)
    """PATHOLOGY LABORATORY
Advanced Diagnostics Center
456 Laboratory Lane, Boston, MA 02102
NABL Accredited | ISO 9001:2015

LABORATORY REPORT

Patient Name: John Michael Smith    Report ID: LAB-2025-001234
Age/Gender: 40 Years / Male         Collection Date: Jan 30, 2025
Ref. by: Dr. Sarah Johnson          Report Date: Jan 31, 2025
Patient ID: PAT-789456              Sample Type: Blood - Serum

COMPLETE BLOOD COUNT (CBC)

TEST            RESULT   UNIT          REFERENCE RANGE
Hemoglobin      14.2     g/dL          13.0 - 17.0
RBC Count       4.8      million/uL    4.5 - 5.5
WBC Count       7.5      thousand/uL   4.0 - 11.0
Platelet Count  250      thousand/uL   150 - 400
Hematocrit      42.5     %             40 - 50
MCV             88       fL            80 - 100
MCH             29.6     pg            27 - 33
MCHC            33.4     g/dL          32 - 36

DIFFERENTIAL COUNT
Neutrophils     62       %             40 - 70
Lymphocytes     30       %             20 - 40
Monocytes       6        %             2 - 10
Eosinophils     2        %             1 - 6
Basophils       0.5      %             0 - 2

COMMENTS: All parameters are within normal limits.

Pathologist: Dr. Robert Chen, MD
Lab Technician: Mary Williams
*** End of Report ***""",

    # Page 7: Cash Receipt
    """CASH RECEIPT

City Medical Center
789 Healthcare Boulevard, Boston, MA 02101

Receipt No: RCP-2025-456789
Date: February 1, 2025
Time: 10:45 AM

Received from: John Michael Smith
Patient ID: PAT-789456

Description                              Amount
------------------------------------------
Consultation Fee - Dr. Sarah Johnson     $150.00
Laboratory Tests (CBC, Blood Sugar)      $80.00
Medications (Prescription)               $45.00
Service Charges                          $10.00
------------------------------------------
TOTAL AMOUNT PAID:                       $285.00

Payment Method: Cash

Thank you for choosing City Medical Center
For any queries: billing@citymedical.com

Cashier Signature: _________________  [OFFICIAL STAMP]""",

    # Page 8: Patient Registration Form (other)
    """PATIENT REGISTRATION FORM
City Medical Center
789 Healthcare Boulevard, Boston, MA 02101

Please fill out this form completely.
All fields marked with * are mandatory.

PERSONAL INFORMATION
* First Name: _______________  * Last Name: _______________
* Date of Birth: ____/____/______
Gender: [ ] Male  [ ] Female  [ ] Other
* Phone Number: (_____)___________
* Address: ___________________________________________________
* City: ______________  * State: _________  * ZIP: ___________

EMERGENCY CONTACT
* Contact Name: _______________________________________________
* Relationship: ______________  * Phone: (_____)___________

INSURANCE INFORMATION
Insurance Provider: ___________________________________________
Policy Number: ____________  Group Number: ____________

CONSENT AND AUTHORIZATION
I hereby consent to medical treatment and authorize City
Medical Center to release my medical information as necessary.

Patient Signature: _______________  Date: _______________""",

    # Page 9: Itemized Hospital Bill
    """ITEMIZED HOSPITAL BILL
City Medical Center
789 Healthcare Boulevard, Boston, MA 02101
Phone: (555) 987-6543

Bill Number: BILL-2025-789456
Bill Date: February 1, 2025
Patient Name: John Michael Smith
Patient ID: PAT-789456
Admission Date: January 20, 2025
Discharge Date: January 25, 2025
Insurance: HealthCare Insurance Co.

ITEMIZED CHARGES

DATE       DESCRIPTION                        QTY  RATE      AMOUNT
01/20/25   Room Charges - Semi-Private         5   $200.00   $1,000.00
01/20/25   Admission Fee                       1   $150.00   $150.00
01/20/25   Emergency Room Services             1   $500.00   $500.00
01/20/25   Physician Consultation              5   $150.00   $750.00
01/20/25   Chest X-Ray                         2   $120.00   $240.00
01/21/25   CT Scan - Chest                     1   $800.00   $800.00
01/20/25   Complete Blood Count (CBC)          3   $45.00    $135.00
01/21/25   Blood Culture Test                  2   $80.00    $160.00
01/22/25   Arterial Blood Gas Analysis         1   $95.00    $95.00
01/20/25   IV Fluids - Normal Saline          10   $25.00    $250.00
01/20/25   Injection - Ceftriaxone 1g          5   $30.00    $150.00
01/21/25   Injection - Paracetamol             6   $8.00     $48.00
01/22/25   Nebulization Treatment              4   $35.00    $140.00
01/20/25   Oxygen Therapy (per hour)          48   $5.00     $240.00
01/20/25   Nursing Care (per day)              5   $100.00   $500.00
01/20/25   ICU Monitoring Equipment            2   $200.00   $400.00
01/23/25   Physiotherapy Session               3   $60.00    $180.00
01/20/25   Medical Supplies & Consumables      1   $250.00   $250.00
01/20/25   Laboratory Processing Fee           1   $75.00    $75.00
01/20/25   Pharmacy Dispensing Fee             1   $50.00    $50.00

                                    Subtotal:       $6,113.00
                                    Tax (5%):       $305.65
                                    Total Amount:   $6,418.65
                          Insurance Payment (80%): -$5,134.92
                        Patient Responsibility:     $1,283.73

Payment due within 30 days from bill date.""",

    # Page 10: Pharmacy Bill (itemized_bill)
    """PHARMACY & OUTPATIENT BILL
City Medical Center
Outpatient Pharmacy Department, Boston, MA 02101

Invoice Number: INV-2025-123789
Date: February 2, 2025
Patient: John Michael Smith (PAT-789456)
Prescribed by: Dr. Sarah Johnson, MD

MEDICATION DETAILS

ITEM                          DOSAGE    QTY  PRICE   TOTAL
Amoxicillin 500mg Capsules    500mg TID  21  $1.50   $31.50
Acetaminophen 500mg Tablets   500mg PRN  20  $0.80   $16.00
Cetirizine 10mg Tablets       10mg OD    10  $0.90   $9.00
Omeprazole 20mg Capsules      20mg BD    14  $1.20   $16.80
Albuterol Inhaler              2 puffs    1  $35.00  $35.00
Vitamin D3 1000 IU            1 tab/day  30  $0.40   $12.00
Probiotic Capsules            1 cap/day  30  $0.85   $25.50
Saline Nasal Spray            As needed   1  $8.50   $8.50
Antiseptic Mouthwash 250ml   Twice daily  1  $12.00  $12.00
Digital Thermometer            N/A        1  $15.00  $15.00

ADDITIONAL SERVICES
Medication Counseling                      1  $25.00  $25.00
Home Delivery Service                      1  $10.00  $10.00

                                  Subtotal:     $216.30
                                  Discount(10%): -$21.63
                                  Tax (6%):      $11.68
                                  TOTAL DUE:     $206.35

Payment Method: Cash / Credit Card / Insurance
Thank you for choosing City Medical Center Pharmacy!""",

    # Page 11: Investigation Report (Metabolic Panel)
    """COMPREHENSIVE METABOLIC PANEL
Advanced Diagnostics Center
456 Laboratory Lane, Boston, MA 02102

Patient: John Michael Smith       Report ID: LAB-2025-001567
DOB: 03/15/1985 (40Y/M)          Collected: Jan 31, 2025
Physician: Dr. Sarah Johnson     Reported: Jan 31, 2025

TEST NAME              RESULT   UNIT            REF RANGE
GLUCOSE METABOLISM
Glucose, Fasting       95       mg/dL           70 - 100
Hemoglobin A1c         5.4      %               < 5.7

KIDNEY FUNCTION
BUN                    18       mg/dL           7 - 20
Creatinine             1.0      mg/dL           0.7 - 1.3
eGFR                   92       mL/min/1.73m2   > 60

LIVER FUNCTION
Total Protein          7.2      g/dL            6.0 - 8.3
Albumin                4.5      g/dL            3.5 - 5.5
Total Bilirubin        0.8      mg/dL           0.1 - 1.2
AST (SGOT)             28       U/L             0 - 40
ALT (SGPT)             32       U/L             0 - 41
Alkaline Phosphatase   75       U/L             30 - 120

ELECTROLYTES
Sodium                 140      mmol/L          136 - 145
Potassium              4.2      mmol/L          3.5 - 5.1
Calcium                9.5      mg/dL           8.5 - 10.5

INTERPRETATION: All parameters within normal limits.
Reviewed by: Dr. Robert Chen, MD, FCAP
*** End of Report ***""",

    # Page 12: Investigation Report (Lipid Panel)
    """LIPID PANEL & THYROID FUNCTION
Advanced Diagnostics Center
456 Laboratory Lane, Boston, MA 02102

Patient: John Michael Smith     Report ID: LAB-2025-001890
Age/Sex: 40 Years / Male        Collected: Feb 1, 2025
Physician: Dr. Sarah Johnson    Reported: Feb 1, 2025

LIPID PANEL (FASTING)
TEST NAME              RESULT  UNIT    REF RANGE         FLAG
Total Cholesterol      195     mg/dL   < 200 Desirable
Triglycerides          145     mg/dL   < 150 Normal
HDL Cholesterol        52      mg/dL   > 40 Normal
LDL Cholesterol        114     mg/dL   < 100 Optimal   BORDERLINE
VLDL Cholesterol       29      mg/dL   5 - 40
Non-HDL Cholesterol    143     mg/dL   < 130 Optimal   BORDERLINE

THYROID FUNCTION TESTS
TSH                    2.5     uIU/mL  0.4 - 4.0
Free T4 (FT4)         1.2     ng/dL   0.8 - 1.8
Free T3 (FT3)         3.1     pg/mL   2.3 - 4.2
Anti-TPO Antibodies    15      IU/mL   < 35

VITAMIN D & OTHER MARKERS
Vitamin D (25-OH)      28      ng/mL   30 - 100        LOW
Vitamin B12            450     pg/mL   200 - 900
Iron                   85      ug/dL   60 - 170
Ferritin               125     ng/mL   30 - 400

*** End of Report ***""",
]


def create_test_pdf(output_path: str = "test_claim.pdf"):
    """Create a multi-page test PDF with sample medical claim content."""
    doc = fitz.open()

    for i, page_text in enumerate(PAGES, 1):
        # A4 size page
        page = doc.new_page(width=595, height=842)
        
        # Add a subtle header bar
        header_rect = fitz.Rect(0, 0, 595, 35)
        page.draw_rect(header_rect, color=(0.2, 0.3, 0.5), fill=(0.2, 0.3, 0.5))
        page.insert_text(
            fitz.Point(20, 24),
            f"Page {i} of {len(PAGES)}",
            fontsize=10,
            color=(1, 1, 1),
            fontname="helv",
        )

        # Insert main text
        text_rect = fitz.Rect(40, 50, 555, 810)
        page.insert_textbox(
            text_rect,
            page_text,
            fontsize=9,
            fontname="helv",
            color=(0.1, 0.1, 0.1),
        )

        # Footer
        page.insert_text(
            fitz.Point(240, 830),
            f"— Page {i} —",
            fontsize=8,
            color=(0.5, 0.5, 0.5),
            fontname="helv",
        )

    doc.save(output_path)
    doc.close()
    print(f"Created test PDF: {output_path} ({len(PAGES)} pages)")
    return output_path


if __name__ == "__main__":
    create_test_pdf()
