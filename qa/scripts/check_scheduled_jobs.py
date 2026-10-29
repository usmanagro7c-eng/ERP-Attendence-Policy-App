import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()

jobs = frappe.get_all(
    'Scheduled Job Type',
    filters={'method': ['like', '%attendance_policy%']},
    fields=['name', 'method', 'frequency', 'cron_format', 'stopped']
)

print(f"Found {len(jobs)} scheduled jobs for attendance_policy:")
for j in jobs:
    print(f"Job: {j.name}, Method: {j.method}, Freq: {j.frequency}, Cron: {j.cron_format}, Stopped: {j.stopped}")
