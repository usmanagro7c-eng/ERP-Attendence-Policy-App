import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()
frappe.db.set_single_value('Attendance Policy Settings', 'habitual_threshold', 2)
frappe.db.commit()
print("habitual_threshold successfully set to 2")
