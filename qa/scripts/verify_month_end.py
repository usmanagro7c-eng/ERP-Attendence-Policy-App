import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from attendance_policy.tasks import month_end_job

frappe.init(site='erp.local')
frappe.connect()

e3 = frappe.db.get_value('Employee', {'first_name': 'QA_E3'})
e5 = frappe.db.get_value('Employee', {'first_name': 'QA_E5'})
e6 = frappe.db.get_value('Employee', {'first_name': 'QA_E6'})

print("--- TC-7.3: QA_E3 Results ---")
lde_e3 = frappe.get_all('Late Deduction Entry', filters={'employee': e3}, fields=['*'])
print("QA_E3 Late Deduction Entries:", [(e.name, e.late_days, e.from_leave, e.from_salary) for e in lde_e3])
lle_e3 = frappe.get_all('Leave Ledger Entry', filters={'employee': e3, 'leaves': ['<', 0]}, fields=['leaves', 'from_date'])
print("QA_E3 Leave Deductions in Ledger:", [(l.leaves, l.from_date) for l in lle_e3])
as_e3 = frappe.get_all('Additional Salary', filters={'employee': e3}, fields=['name', 'amount'])
print("QA_E3 Additional Salaries:", as_e3)

print("\n--- TC-7.4: QA_E5 Results ---")
lde_e5 = frappe.get_all('Late Deduction Entry', filters={'employee': e5}, fields=['*'])
print("QA_E5 Late Deduction Entries:", [(e.name, e.late_days, e.from_leave, e.from_salary) for e in lde_e5])
lle_e5 = frappe.get_all('Leave Ledger Entry', filters={'employee': e5, 'leaves': ['<', 0]}, fields=['leaves', 'from_date'])
print("QA_E5 Leave Deductions in Ledger:", [(l.leaves, l.from_date) for l in lle_e5])
as_e5 = frappe.get_all('Additional Salary', filters={'employee': e5}, fields=['name', 'salary_component', 'amount', 'payroll_date', 'docstatus'])
print("QA_E5 Additional Salaries:", [(a.name, a.salary_component, a.amount, a.payroll_date, a.docstatus) for a in as_e5])

print("\n--- TC-7.5: QA_E6 Results ---")
lde_e6 = frappe.get_all('Late Deduction Entry', filters={'employee': e6})
print("QA_E6 Late Deduction Entries (should be empty):", lde_e6)

print("\n--- TC-7.6: Log Status Check ---")
e3_logs = frappe.get_all('Late Arrival Log', filters={'employee': e3}, fields=['name', 'status', 'deduction_entry'])
e5_logs = frappe.get_all('Late Arrival Log', filters={'employee': e5}, fields=['name', 'status', 'deduction_entry'])
print("QA_E3 logs:", [(l.name, l.status, l.deduction_entry) for l in e3_logs])
print("QA_E5 logs:", [(l.name, l.status, l.deduction_entry) for l in e5_logs])

print("\n--- TC-7.7: Idempotency Check (Run 2nd time) ---")
count_entries_before = frappe.db.count('Late Deduction Entry')
count_as_before = frappe.db.count('Additional Salary')
month_end_job('2026-10-31')
count_entries_after = frappe.db.count('Late Deduction Entry')
count_as_after = frappe.db.count('Additional Salary')
print(f"Entries: before={count_entries_before}, after={count_entries_after}")
print(f"Additional Salaries: before={count_as_before}, after={count_as_after}")
if count_entries_before == count_entries_after and count_as_before == count_as_after:
    print("TC-7.7 IDEMPOTENCY PASS: No duplicates created on rerun")
else:
    print("TC-7.7 IDEMPOTENCY FAIL: Duplicates detected!")
