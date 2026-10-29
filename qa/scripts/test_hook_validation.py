import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from attendance_policy.leave_rules import validate_leave_application

frappe.init(site='erp.local')
frappe.connect()

emp1 = frappe.db.get_value('Employee', {'first_name': 'QA_E1'})

doc_no_reason = frappe.new_doc('Leave Application')
doc_no_reason.employee = emp1
doc_no_reason.leave_type = 'Casual Leave'
doc_no_reason.from_date = '2026-11-02'
doc_no_reason.to_date = '2026-11-02'
doc_no_reason.leave_approver = 'admin@example.com'
doc_no_reason.description = ''

try:
    validate_leave_application(doc_no_reason)
    print("TC-6.2_no_reason => ALLOWED (UNEXPECTED)")
except Exception as e:
    print(f"TC-6.2_no_reason => BLOCKED: {e}")

doc_reason = frappe.new_doc('Leave Application')
doc_reason.employee = emp1
doc_reason.leave_type = 'Casual Leave'
doc_reason.from_date = '2026-11-02'
doc_reason.to_date = '2026-11-02'
doc_reason.leave_approver = 'admin@example.com'
doc_reason.description = 'Personal urgent work'

try:
    validate_leave_application(doc_reason)
    print("TC-6.2_with_reason => ALLOWED")
except Exception as e:
    print(f"TC-6.2_with_reason => BLOCKED: {e}")
