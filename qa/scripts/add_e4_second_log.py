import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()

e4 = frappe.db.get_value('Employee', {'first_name': 'QA_E4'})
doc = frappe.new_doc('Late Arrival Log')
doc.employee = e4
doc.employee_name = 'QA_E4'
doc.attendance_date = '2026-10-06'
doc.grade = 'Grade 2'
doc.deduction_days = 0.333333
doc.arrival_time = '10:10:00'
doc.exit_time = '17:30:00'
doc.status = 'Pending'
doc.insert(ignore_permissions=True)
frappe.db.commit()

from attendance_policy.attendance_policy.report.habitual_late_comers.habitual_late_comers import execute
columns, data, message, chart = execute({'from_date': '2026-10-01', 'to_date': '2026-10-31'})
print("Employees returned after adding 2nd log for QA_E4 (threshold=2):")
for row in data:
    print(f"Employee: {row['employee_name']}, Total: {row['total']}, Days: {row['days']}")
