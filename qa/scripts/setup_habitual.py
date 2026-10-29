import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from frappe.utils import getdate

frappe.init(site='erp.local')
frappe.connect()

e3 = frappe.db.get_value('Employee', {'first_name': 'QA_E3'})
e4 = frappe.db.get_value('Employee', {'first_name': 'QA_E4'})

# Clear existing logs for e3 and e4 in Oct 2026
for l in frappe.get_all('Late Arrival Log', filters={'employee': ['in', [e3, e4]]}):
    frappe.delete_doc('Late Arrival Log', l.name, force=True)

frappe.db.commit()

e3_logs = [
    ('2026-10-05', 'Grade 1', 0.166667, '09:15:00', '17:30:00'),
    ('2026-10-06', 'Grade 2', 0.333333, '10:15:00', '17:30:00'),
    ('2026-10-07', 'Grade 3', 0.500000, '11:15:00', '17:30:00'),
    ('2026-10-08', 'Grade 1', 0.166667, '09:20:00', '17:30:00')
]

for dt, gr, ded, arr, ex in e3_logs:
    doc = frappe.new_doc('Late Arrival Log')
    doc.employee = e3
    doc.employee_name = 'QA_E3'
    doc.attendance_date = dt
    doc.grade = gr
    doc.deduction_days = ded
    doc.arrival_time = arr
    doc.exit_time = ex
    doc.status = 'Pending'
    doc.insert(ignore_permissions=True)

e4_logs = [
    ('2026-10-05', 'Grade 1', 0.166667, '09:10:00', '17:30:00')
]

for dt, gr, ded, arr, ex in e4_logs:
    doc = frappe.new_doc('Late Arrival Log')
    doc.employee = e4
    doc.employee_name = 'QA_E4'
    doc.attendance_date = dt
    doc.grade = gr
    doc.deduction_days = ded
    doc.arrival_time = arr
    doc.exit_time = ex
    doc.status = 'Pending'
    doc.insert(ignore_permissions=True)

frappe.db.commit()
print("Setup habitual late logs for QA_E3 (4) and QA_E4 (1) successfully")
