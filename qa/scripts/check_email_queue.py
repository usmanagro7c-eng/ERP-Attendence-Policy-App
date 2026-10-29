import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe

frappe.init(site='erp.local')
frappe.connect()

emails = frappe.get_all(
    'Email Queue',
    fields=['name', 'sender', 'status', 'creation'],
    order_by='creation desc',
    limit=5
)

print(f"Total recent emails: {len(emails)}")
for e in emails:
    recipients = frappe.get_all('Email Queue Recipient', filters={'parent': e.name}, fields=['recipient'])
    rec_list = [r.recipient for r in recipients]
    print(f"{e.name}: Status={e.status}, Sender={e.sender}, Recipients={rec_list}, Created={e.creation}")
    # get email body
    comm = frappe.get_value('Email Queue', e.name, 'message')
    print("Subject / Header:", comm[:200] if comm else "No message")
