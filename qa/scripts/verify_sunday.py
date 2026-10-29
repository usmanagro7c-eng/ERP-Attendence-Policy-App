import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from frappe.utils import getdate

frappe.init(site='erp.local')
frappe.connect()

logs_sunday = frappe.get_all('Late Arrival Log', filters={'attendance_date': '2026-10-18'})
print(f"Total Late Arrival Logs for Sunday 2026-10-18: {len(logs_sunday)}")
