import os
import sys

os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

e3 = frappe.db.get_value('Employee', {'first_name': 'QA_E3'})
e5 = frappe.db.get_value('Employee', {'first_name': 'QA_E5'})

print(f"QA_E3: {e3}, QA_E5: {e5}")

# Clean existing salary slips for e3 and e5 for Oct 2026
for ss in frappe.get_all('Salary Slip', filters={'employee': ['in', [e3, e5]], 'start_date': '2026-10-01'}):
    frappe.delete_doc('Salary Slip', ss.name, force=True)
frappe.db.commit()

# Generate Salary Slip for QA_E5
ss5 = make_salary_slip('QA_Salary_Structure', employee=e5, print_format=None, posting_date='2026-10-31')
ss5.start_date = '2026-10-01'
ss5.end_date = '2026-10-31'
ss5.insert(ignore_permissions=True)
ss5.calculate_net_pay()
ss5.save()

print("--- QA_E5 Salary Slip ---")
print(f"Name: {ss5.name}, Gross Pay: {ss5.gross_pay}, Total Deduction: {ss5.total_deduction}, Net Pay: {ss5.net_pay}")
for d in ss5.deductions:
    print(f"  Deduction: {d.salary_component} = {d.amount}")

# Generate Salary Slip for QA_E3
ss3 = make_salary_slip('QA_Salary_Structure', employee=e3, print_format=None, posting_date='2026-10-31')
ss3.start_date = '2026-10-01'
ss3.end_date = '2026-10-31'
ss3.insert(ignore_permissions=True)
ss3.calculate_net_pay()
ss3.save()

print("\n--- QA_E3 Salary Slip ---")
print(f"Name: {ss3.name}, Gross Pay: {ss3.gross_pay}, Total Deduction: {ss3.total_deduction}, Net Pay: {ss3.net_pay}")
for d in ss3.deductions:
    print(f"  Deduction: {d.salary_component} = {d.amount}")

frappe.db.commit()
