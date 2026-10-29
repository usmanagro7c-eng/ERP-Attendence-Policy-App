import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()

msg = frappe.get_value('Email Queue', 'v4ucl7ktd5', 'message')
print("FULL_EMAIL_SNIPPET:")
print(msg[:3000] if msg else "EMPTY")
