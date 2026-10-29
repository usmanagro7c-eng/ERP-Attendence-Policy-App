import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

from attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings import process_month_end

emp_ok_id = frappe.db.get_value("Employee", {"first_name": "QA_OK_SSA"}, "name")
test_date = "2027-01-15"
period_end = "2027-01-31"

# Create a test log for Jan 2027
log = frappe.get_doc({
    "doctype": "Late Arrival Log",
    "employee": emp_ok_id,
    "attendance_date": test_date,
    "in_time": "10:30:00",
    "grade": "Grade 2",
    "deduction_days": 0.333333,
    "status": "Pending"
}).insert(ignore_permissions=True)
frappe.db.commit()

# Test 1: dry_run = True
res_dry = process_month_end(period_end=period_end, dry_run=True)
print("--- Dry Run Result ---")
print(res_dry)
log.reload()
print(f"Log status after dry run: {log.status} (expected Pending)")

# Test 2: non-last day
try:
    process_month_end(period_end="2027-01-20", dry_run=True)
    print("Non-last day test: FAILED (should have thrown error)")
except Exception as e:
    print(f"Non-last day test: PASSED (threw: {e})")

# Test 3: dry_run = False (commit)
res_commit = process_month_end(period_end=period_end, dry_run=False)
print("\n--- Commit Result ---")
print(res_commit)
log.reload()
print(f"Log status after commit: {log.status} (expected Processed)")
print(f"Linked entry: {log.deduction_entry}")
