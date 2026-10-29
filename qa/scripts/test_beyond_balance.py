import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()

emp5 = frappe.db.get_value('Employee', {'first_name': 'QA_E5'})
la = frappe.new_doc('Leave Application')
la.employee = emp5
la.leave_type = 'Casual Leave'
la.from_date = '2026-11-17'
la.to_date = '2026-11-17'
la.total_leave_days = 1
la.leave_approver = 'admin@example.com'
la.description = 'Personal emergency'

try:
    la.insert(ignore_permissions=True)
    print("Leave beyond balance: ALLOWED on insert, docstatus =", la.docstatus)
except Exception as e:
    print("Leave beyond balance: BLOCKED on insert with:", e)
