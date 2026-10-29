import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from frappe.utils import getdate

frappe.init(site='erp.local')
frappe.connect()

e3 = frappe.db.get_value('Employee', {'first_name': 'QA_E3'})
e5 = frappe.db.get_value('Employee', {'first_name': 'QA_E5'})
e6 = frappe.db.get_value('Employee', {'first_name': 'QA_E6'})

# 1. Clean existing logs, deduction entries, and additional salaries for Oct 2026 for e3, e5, e6
for dt in ['Late Deduction Entry', 'Additional Salary']:
    for doc in frappe.get_all(dt, filters={'employee': ['in', [e3, e5, e6]], 'docstatus': ['<', 2]}):
        frappe.delete_doc(dt, doc.name, force=True)

for l in frappe.get_all('Late Arrival Log', filters={'employee': ['in', [e3, e5, e6]]}):
    frappe.delete_doc('Late Arrival Log', l.name, force=True)

frappe.db.commit()

# Ensure QA_E5 has exactly 0.2 casual leave balance
la5_name = frappe.db.get_value('Leave Allocation', {'employee': e5, 'leave_type': 'Casual Leave', 'docstatus': 1})
if la5_name:
    frappe.db.set_value('Leave Allocation', la5_name, 'total_leaves_allocated', 0.2)
    frappe.db.set_value('Leave Allocation', la5_name, 'new_leaves_allocated', 0.2)
    # Clear any past leave ledger entries for e5
    frappe.db.sql("DELETE FROM `tabLeave Ledger Entry` WHERE employee = %s", e5)
    # Re-insert allocation ledger entry
    frappe.get_doc('Leave Allocation', la5_name).create_leave_ledger_entry()

# Ensure QA_E3 has 15 casual leave balance
la3_name = frappe.db.get_value('Leave Allocation', {'employee': e3, 'leave_type': 'Casual Leave', 'docstatus': 1})
if la3_name:
    frappe.db.set_value('Leave Allocation', la3_name, 'total_leaves_allocated', 15)
    frappe.db.set_value('Leave Allocation', la3_name, 'new_leaves_allocated', 15)
    frappe.db.sql("DELETE FROM `tabLeave Ledger Entry` WHERE employee = %s", e3)
    frappe.get_doc('Leave Allocation', la3_name).create_leave_ledger_entry()

frappe.db.commit()

# Create Pending logs totalling 1.0 day for QA_E3 (e.g. 2 logs of 0.5 day)
for d, arr in [('2026-10-12', '11:15:00'), ('2026-10-13', '11:20:00')]:
    doc = frappe.new_doc('Late Arrival Log')
    doc.employee = e3
    doc.employee_name = 'QA_E3'
    doc.attendance_date = d
    doc.grade = 'Grade 3'
    doc.deduction_days = 0.5
    doc.arrival_time = arr
    doc.exit_time = '17:30:00'
    doc.status = 'Pending'
    doc.insert(ignore_permissions=True)

# Create Pending logs totalling 1.0 day for QA_E5 (e.g. 2 logs of 0.5 day)
for d, arr in [('2026-10-12', '11:15:00'), ('2026-10-13', '11:20:00')]:
    doc = frappe.new_doc('Late Arrival Log')
    doc.employee = e5
    doc.employee_name = 'QA_E5'
    doc.attendance_date = d
    doc.grade = 'Grade 3'
    doc.deduction_days = 0.5
    doc.arrival_time = arr
    doc.exit_time = '17:30:00'
    doc.status = 'Pending'
    doc.insert(ignore_permissions=True)

frappe.db.commit()
print("Phase 7 test setup completed successfully!")
