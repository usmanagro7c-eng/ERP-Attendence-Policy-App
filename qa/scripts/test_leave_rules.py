import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from frappe.utils import getdate

frappe.init(site='erp.local')
frappe.connect()

emp1 = frappe.db.get_value('Employee', {'first_name': 'QA_E1'})
emp2 = frappe.db.get_value('Employee', {'first_name': 'QA_E2'})

results = {}

# TC-6.1: Casual leave 3 days (e.g. 2026-11-03 to 2026-11-05: Tue, Wed, Thu)
doc3 = frappe.new_doc('Leave Application')
doc3.employee = emp1
doc3.leave_type = 'Casual Leave'
doc3.from_date = '2026-11-03'
doc3.to_date = '2026-11-05'
doc3.leave_approver = 'admin@example.com'
try:
    doc3.validate()
    results['TC-6.1_3_days'] = 'ALLOWED'
except Exception as e:
    results['TC-6.1_3_days'] = f'ERROR: {e}'

# TC-6.1: Casual leave 4 days (2026-11-03 to 2026-11-06)
doc4 = frappe.new_doc('Leave Application')
doc4.employee = emp1
doc4.leave_type = 'Casual Leave'
doc4.from_date = '2026-11-03'
doc4.to_date = '2026-11-06'
doc4.leave_approver = 'admin@example.com'
try:
    doc4.validate()
    results['TC-6.1_4_days'] = 'ALLOWED (UNEXPECTED)'
except Exception as e:
    results['TC-6.1_4_days'] = f'BLOCKED: {e}'

# TC-6.2: Adjacent to Sunday without Reason
# 2026-11-02 is Monday (right after Sunday Nov 01)
doc_no_reason = frappe.new_doc('Leave Application')
doc_no_reason.employee = emp1
doc_no_reason.leave_type = 'Casual Leave'
doc_no_reason.from_date = '2026-11-02'
doc_no_reason.to_date = '2026-11-02'
doc_no_reason.leave_approver = 'admin@example.com'
doc_no_reason.description = ''
try:
    doc_no_reason.validate()
    results['TC-6.2_no_reason'] = 'ALLOWED (UNEXPECTED)'
except Exception as e:
    results['TC-6.2_no_reason'] = f'BLOCKED: {e}'

# With Reason
doc_reason = frappe.new_doc('Leave Application')
doc_reason.employee = emp1
doc_reason.leave_type = 'Casual Leave'
doc_reason.from_date = '2026-11-02'
doc_reason.to_date = '2026-11-02'
doc_reason.leave_approver = 'admin@example.com'
doc_reason.description = 'Personal family event'
try:
    doc_reason.validate()
    results['TC-6.2_with_reason'] = 'ALLOWED'
except Exception as e:
    results['TC-6.2_with_reason'] = f'BLOCKED: {e}'

# TC-6.3: Annual leave for QA_E2 (<12 months, joined 2026-07-28)
doc_ann_e2 = frappe.new_doc('Leave Application')
doc_ann_e2.employee = emp2
doc_ann_e2.leave_type = 'Annual Leave'
doc_ann_e2.from_date = '2026-11-10'
doc_ann_e2.to_date = '2026-11-12'
doc_ann_e2.leave_approver = 'admin@example.com'
try:
    doc_ann_e2.validate()
    results['TC-6.3_QA_E2'] = 'ALLOWED (UNEXPECTED)'
except Exception as e:
    results['TC-6.3_QA_E2'] = f'BLOCKED: {e}'

# Annual leave for QA_E1 (>12 months, joined 2025-01-01) with future dates
doc_ann_e1 = frappe.new_doc('Leave Application')
doc_ann_e1.employee = emp1
doc_ann_e1.leave_type = 'Annual Leave'
doc_ann_e1.from_date = '2026-11-10'
doc_ann_e1.to_date = '2026-11-12'
doc_ann_e1.leave_approver = 'admin@example.com'
try:
    doc_ann_e1.validate()
    results['TC-6.3_QA_E1'] = 'ALLOWED'
except Exception as e:
    results['TC-6.3_QA_E1'] = f'BLOCKED: {e}'

for k, v in results.items():
    print(f"{k} => {v}")
