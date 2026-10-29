import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

company = frappe.db.get_value("Salary Structure", "QA_Salary_Structure", "company")
accs = frappe.get_all("Account", filters={"company": company, "is_group": 0, "account_type": ["not in", ["Receivable", "Payable"]]}, fields=["name", "account_type"], limit=10)
for a in accs:
    print(a.name, a.account_type)
