import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

company = frappe.db.get_value("Salary Structure", "QA_Salary_Structure", "company")
print(f"Company: {company}")

# Find two accounts for company
accounts = frappe.get_all("Account", filters={"company": company, "is_group": 0}, fields=["name", "account_type"], limit=10)
print(f"Available accounts: {[a.name for a in accounts[:4]]}")

acc1 = "Prepaid Expenses - UD"
acc2 = "Cash - UD"

# 1. Update Attendance Policy Settings
settings = frappe.get_single("Attendance Policy Settings")
old_create_je = settings.create_journal_entry
old_debit = settings.je_debit_account
old_credit = settings.je_credit_account

settings.create_journal_entry = 1
settings.je_debit_account = acc1
settings.je_credit_account = acc2
settings.save(ignore_permissions=True)
frappe.db.commit()
print(f"Updated Settings: create_journal_entry=1, debit={acc1}, credit={acc2}")

# 2. Setup QA_OK_SSA for 2026-12
emp_ok_id = frappe.db.get_value("Employee", {"first_name": "QA_OK_SSA"}, "name")
test_date = "2026-12-10"
period_end = "2026-12-31"

# Clean old logs
frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee = %s AND attendance_date >= '2026-12-01'", emp_ok_id)
frappe.db.commit()

log = frappe.get_doc({
    "doctype": "Late Arrival Log",
    "employee": emp_ok_id,
    "attendance_date": test_date,
    "in_time": "11:30:00",
    "grade": "Grade 3",
    "deduction_days": 0.5,
    "status": "Pending"
}).insert(ignore_permissions=True)
frappe.db.commit()

# Run month_end_job
from attendance_policy.tasks import month_end_job
try:
    month_end_job(date=period_end)
except Exception as e:
    import traceback
    traceback.print_exc()

errs = frappe.get_all("Error Log", fields=["method", "error"], order_by="creation desc", limit=1)
if errs:
    print(f"Latest Error Log Method: {errs[0].method}")
    print(f"Latest Error Log Content:\n{errs[0].error}")

# Verify Late Deduction Entry and Journal Entry
lde = frappe.get_all("Late Deduction Entry", filters={"employee": emp_ok_id, "period_end": period_end}, fields=["name", "journal_entry", "salary_amount", "additional_salary"])
print(f"Late Deduction Entry result: {lde}")

je_name = None
if lde and lde[0].journal_entry:
    je_name = lde[0].journal_entry
    je_doc = frappe.get_doc("Journal Entry", je_name)
    print(f"Journal Entry created: {je_doc.name}, posting_date: {je_doc.posting_date}, total_debit: {je_doc.total_debit}, docstatus: {je_doc.docstatus}")

# Revert settings
settings.reload()
settings.create_journal_entry = old_create_je
settings.je_debit_account = old_debit
settings.je_credit_account = old_credit
settings.save(ignore_permissions=True)
frappe.db.commit()
print(f"Reverted Settings: create_journal_entry={settings.create_journal_entry}")

if je_name:
    print("TC-7.10 PASS: Journal Entry created and linked successfully!")
else:
    print("TC-7.10 FAIL: Journal Entry was NOT created.")
