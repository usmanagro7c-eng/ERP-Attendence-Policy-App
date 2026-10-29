import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from attendance_policy.tasks import daily_job

frappe.init(site='erp.local')
frappe.connect()

# Count emails before
before_count = frappe.db.count('Email Queue')

# Set report_recipients to empty
orig = frappe.db.get_single_value('Attendance Policy Settings', 'report_recipients')
frappe.db.set_single_value('Attendance Policy Settings', 'report_recipients', '')
frappe.db.commit()

# Run daily_job
error = None
try:
    daily_job('2026-10-21')
    print("daily_job ran without exception on empty recipients")
except Exception as e:
    error = str(e)
    print("daily_job failed on empty recipients:", error)

# Restore recipients
frappe.db.set_single_value('Attendance Policy Settings', 'report_recipients', orig)
frappe.db.commit()

after_count = frappe.db.count('Email Queue')
print(f"Emails before: {before_count}, Emails after: {after_count}")
if error is None and after_count == before_count:
    print("TC-4.3 PASS: No crash and no email queued when recipients empty")
else:
    print(f"TC-4.3 FAIL: error={error}, diff={after_count - before_count}")
