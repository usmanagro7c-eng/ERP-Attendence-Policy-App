import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()

for emp in frappe.get_all('Employee'):
    frappe.db.set_value('Employee', emp.name, 'leave_approver', 'admin@example.com')
frappe.db.commit()
print("Updated leave_approver for all employees to admin@example.com")
