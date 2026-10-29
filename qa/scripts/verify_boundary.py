import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from frappe.utils import getdate

frappe.init(site='erp.local')
frappe.connect()

test_date = getdate('2026-10-21')

logs = frappe.get_all(
    'Late Arrival Log',
    filters={'attendance_date': test_date},
    fields=['name', 'employee', 'employee_name', 'grade', 'deduction_days', 'arrival_time', 'exit_time', 'status'],
    order_by='employee_name asc'
)

print(f"Total Late Arrival Logs for {test_date}: {len(logs)}")
for l in logs:
    print(f"{l.employee_name} ({l.employee}): Grade={l.grade}, Days={l.deduction_days}, In={l.arrival_time}, Out={l.exit_time}, Status={l.status}")
