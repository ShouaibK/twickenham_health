import sys
import os
# Ensure project root is on sys.path when running this test script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from logic.pdf_generator import generate_pdf

invoice = {
    'inv_no': 'THL-GPTEST',
    'inv_date': '2026-06-20',
    'due_date': '2026-07-04',
    'ref': 'TEST',
    'net_amount': 350.0,
    'due_amount': 350.0,
    'sessions': [
        {
            'sr_no': 1,
            'activity': 'Locum GP session',
            'job_date': '2026-06-19',
            'hour_rate': 350.0,
            'work_hours': 'Duty Session',
            'session_total': 350.0,
        }
    ]
}

try:
    path = generate_pdf(invoice)
    print('PDF_CREATED:', path)
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR:', e)
