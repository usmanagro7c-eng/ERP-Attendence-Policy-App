import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

# 1. Create QA_NO_SSA employee if not exists
emp_name = "QA_NO_SSA"
emp_id = frappe.db.get_value("Employee", {"first_name": emp_name}, "name")
if not emp_id:
    company = frappe.db.get_value("Salary Structure", "QA_Salary_Structure", "company")
    emp_id = frappe.db.get_value("Employee", {"first_name": emp_name}, "name")
    if not emp_id:
        emp = frappe.get_doc({
            "doctype": "Employee",
            "first_name": emp_name,
            "company": company,
            "gender": "Female",
            "date_of_birth": "1995-01-01",
            "date_of_joining": "2026-04-01",
            "status": "Active"
        }).insert(ignore_permissions=True)
        emp_id = emp.name
        print(f"Created {emp_name} with ID: {emp_id}")
    else:
        print(f"Found {emp_name} with ID: {emp_id}")
        frappe.db.set_value("Employee", emp_id, "company", company)

# Ensure NO Salary Structure Assignment exists for emp_id
for ssa in frappe.get_all("Salary Structure Assignment", filters={"employee": emp_id}):
    frappe.delete_doc("Salary Structure Assignment", ssa.name, force=True)

# Also create another employee WITH Salary Structure Assignment to verify "others still processed"
emp_ok_name = "QA_OK_SSA"
emp_ok_id = frappe.db.get_value("Employee", {"first_name": emp_ok_name}, "name")
if not emp_ok_id:
    company = frappe.db.get_value("Employee", emp_id, "company")
    emp_ok = frappe.get_doc({
        "doctype": "Employee",
        "first_name": emp_ok_name,
        "company": company,
        "gender": "Male",
        "date_of_birth": "1994-01-01",
        "date_of_joining": "2026-04-01",
        "status": "Active"
    }).insert(ignore_permissions=True)
    emp_ok_id = emp_ok.name
    
    # Assign salary structure
    ssa = frappe.get_doc({
        "doctype": "Salary Structure Assignment",
        "employee": emp_ok_id,
        "salary_structure": "QA_Salary_Structure",
        "from_date": "2026-04-01",
        "base": 60000,
        "company": company,
        "docstatus": 1
    }).insert(ignore_permissions=True)
    print(f"Created {emp_ok_name} with ID: {emp_ok_id} and SSA")

# Clean existing logs for both for 2026-11
test_month = "2026-11-30" # November last day
test_date = "2026-11-05"

frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee IN (%s, %s)", (emp_id, emp_ok_id))
frappe.db.commit()

# Create Pending log for QA_NO_SSA
log_no_ssa = frappe.get_doc({
    "doctype": "Late Arrival Log",
    "employee": emp_id,
    "attendance_date": test_date,
    "in_time": "10:30:00",
    "grade": "Grade 2",
    "deduction_days": 0.333333,
    "status": "Pending"
}).insert(ignore_permissions=True)

# Create Pending log for QA_OK_SSA
log_ok = frappe.get_doc({
    "doctype": "Late Arrival Log",
    "employee": emp_ok_id,
    "attendance_date": test_date,
    "in_time": "10:30:00",
    "grade": "Grade 2",
    "deduction_days": 0.333333,
    "status": "Pending"
}).insert(ignore_permissions=True)

frappe.db.commit()
print(f"Created pending logs: {log_no_ssa.name} for {emp_id}, {log_ok.name} for {emp_ok_id}")

# Count Error Logs before
error_logs_before = frappe.db.count("Error Log")

# Execute month_end_job for 2026-11-30
from attendance_policy.tasks import month_end_job
month_end_job(date=test_month)

# Check status of logs
log_no_ssa.reload()
log_ok.reload()
print(f"QA_NO_SSA log status: {log_no_ssa.status}")
print(f"QA_OK_SSA log status: {log_ok.status}")

# Check Error Log
new_errors = frappe.get_all("Error Log", fields=["method", "error"], order_by="creation desc", limit=3)
print(f"New error logs:")
for err in new_errors:
    print(f"  Method: {err.method}, Error: {err.error[:150]}...")
