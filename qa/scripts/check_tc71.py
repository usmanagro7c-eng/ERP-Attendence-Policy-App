import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()

entries = frappe.get_all('Late Deduction Entry', fields=['name', 'employee'])
pending = frappe.db.count('Late Arrival Log', {'status': 'Pending'})
print(f"Late Deduction Entries: {len(entries)}, Pending Logs: {pending}")
