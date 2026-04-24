from pathlib import Path
from app import create_app
from tests.test_api import TestConfig
import time

app = create_app(TestConfig)
client = app.test_client()
sample_pdf = Path('sample-dataset/invoices/invoice-001-standard.pdf')
with sample_pdf.open('rb') as f:
    response = client.post(
        '/api/invoices/batch',
        data={'files': (f, 'invoice-001-standard.pdf')},
        content_type='multipart/form-data',
    )
print('post status', response.status_code, response.get_json())
job_id = response.get_json()['job_id']
status = None
for i in range(20):
    status = client.get(f'/api/invoices/batch/{job_id}').get_json()
    print('poll', i, status['status'], status['completed'], status.get('results'))
    if status['status'] == 'finished':
        break
    time.sleep(0.2)
print('final status', status)
