#!/usr/bin/env python
"""Test invoice validation with sample PDF."""
import requests
import os
import json

# Test with a valid invoice PDF
invoice_path = 'sample-dataset/invoices/invoice-001-standard.pdf'
if os.path.exists(invoice_path):
    with open(invoice_path, 'rb') as f:
        files = {'files': ('invoice-001.pdf', f, 'application/pdf')}
        response = requests.post('http://127.0.0.1:5000/api/invoices', files=files)
        print(f'Status: {response.status_code}')
        result = response.json()
        
        if result['invoices']:
            invoice = result['invoices'][0]
            print(f"\nInvoice Processing Result:")
            print(f"Status: {invoice.get('status')}")
            if 'error' in invoice:
                print(f"Error: {invoice.get('error')}")
            else:
                print(f"Invoice ID: {invoice.get('id')}")
                print(f"Filename: {invoice.get('original_filename')}")
                extraction = invoice.get('extraction', {})
                if extraction:
                    print(f"\nExtracted Fields:")
                    for key, value in extraction.items():
                        if key != 'source':
                            print(f"  {key}: {value}")
else:
    print('Invoice PDF not found at', invoice_path)
