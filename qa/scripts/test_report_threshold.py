import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from attendance_policy.attendance_policy.report.habitual_late_comers.habitual_late_comers import execute

frappe.init(site='erp.local')
frappe.connect()

columns, data, message, chart = execute({'from_date': '2026-10-01', 'to_date': '2026-10-31'})
print("Employees returned with threshold 2:")
for row in data:
    print(f"Employee: {row['employee_name']}, Total: {row['total']}, Days: {row['days']}")
