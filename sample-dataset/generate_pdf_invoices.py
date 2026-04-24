from pathlib import Path


INVOICES = {
    "invoice-001-standard.pdf": """
Greenfield Office Supplies Pvt Ltd
Tax Invoice
Vendor GSTIN: 29ABCDE1234F1Z5
Vendor PAN: ABCDE1234F
Address: 42 Market Street, Sector 7, Bengaluru, Karnataka 560001
Contact Person: Priya Raman, +91 9876543210, priya.raman@example.com
UPI: greenfield@okaxis
Bank Account Number: 123456789012
IFSC: HDFC0001234

Bill To: Arun Mehta, 18 Finance Road, Mumbai, Maharashtra 400001

Invoice No: INV-2026-001
Invoice Date: 20/04/2026
Due Date: 30/04/2026

Description                         Qty      Rate        Amount
A4 copier paper cartons              10    850.00      8,500.00
Desk organizers                        5    700.00      3,500.00

Subtotal: INR 12,000.00
GST: INR 2,160.00
Total Amount: INR 14,160.00
""",
    "invoice-002-missing-total.pdf": """
Northstar Facilities Services
Tax Invoice
Vendor GSTIN: 27PQRSX9876L1Z8
Contact Person: Kavita Iyer, +91 9123456789, kavita.iyer@example.net
Address: Floor 3, Tower B, East Park Road, Pune, Maharashtra 411001

Bill To: Neha Kapoor, 77 Accounts Lane, Chennai, Tamil Nadu 600001

Invoice No: FAC-2026-019
Invoice Date: 19/04/2026
Due Date: 05/05/2026

Description                         Qty      Rate        Amount
Office deep cleaning                  1   5,000.00     5,000.00
Pantry maintenance                    1   2,500.00     2,500.00

Subtotal: INR 7,500.00
Tax: INR 1,350.00
Amount payable: Not printed on source invoice
""",
    "invoice-003-usd-services.pdf": """
Blue Ridge Software LLC
Invoice
Contact Person: Maya Stone, +1 415 555 0198, billing@blueridge.example
Address: 210 Pine Street, Suite 400, San Francisco, CA 94104
Bank Account Number: 555666777888

Prepared For: Daniel Lee, 55 Corporate Plaza, New York, NY 10005

Invoice Number: US-2026-044
Invoice Date: 2026-04-18
Payment Due: 2026-05-18

Description                         Qty      Rate        Amount
Workflow automation support           6    USD 150.00   USD 900.00
Monthly hosting                       1    USD 250.00   USD 250.00

Invoice Total: USD 1,150.00
""",
    "invoice-004-noisy-ocr.pdf": """
Metro Industrial Traders Pvt Ltd
TAX lNVOICE
Vendor GSTIN: 07LMNOP4321Q1Z3
PAN: LMNOP4321Q
Contact Person: Rohit Sen +91 9988776655 rohit.sen@example.org
A/c No: 998877665544
IFSC: ICIC0005678
Ship To: Sima Rao, Plot 12, Phase 2, Noida, Uttar Pradesh 201301

Inv No: MIT/26/0098
Date: 21-04-2026
Due Date: 01-05-2026

Description                         Qty      Rate        Amount
Safety gloves boxes                   20    250.00      5,000.00
Protective goggles                    15    300.00      4,500.00

Grand Tota1: INR 9,500.00
""",
}


def main():
    output_dir = Path(__file__).resolve().parent / "invoices"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, text in INVOICES.items():
        create_pdf(output_dir / filename, text)
        print(f"created {output_dir / filename}")


def create_pdf(path, text):
    lines = [line.rstrip() for line in text.strip().splitlines()]
    stream = build_text_stream(lines)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream",
    ]
    path.write_bytes(build_pdf(objects))


def build_text_stream(lines):
    commands = ["BT", "/F1 10 Tf", "50 760 Td", "13 TL"]
    for line in lines:
        commands.append(f"({escape_pdf_text(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("ascii")


def build_pdf(objects):
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_start}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def escape_pdf_text(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


if __name__ == "__main__":
    main()
