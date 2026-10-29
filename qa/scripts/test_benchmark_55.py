import os
import time
from datetime import datetime, timedelta
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

from attendance_policy.tasks import daily_job

test_date_50 = "2026-11-13"
frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE attendance_date = %s", test_date_50)
frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE date(time) = %s", test_date_50)
frappe.db.commit()

# Create or reuse employees to get 55 checkins
active_emps = [e.name for e in frappe.get_all("Employee", filters={"status": "Active"})]
company = frappe.db.get_value("Employee", active_emps[0], "company")

# If less than 55, create temporary employees
needed = 55 - len(active_emps)
if needed > 0:
    for i in range(needed):
        e = frappe.get_doc({
            "doctype": "Employee",
            "first_name": f"QA_BENCH_{i}",
            "company": company,
            "gender": "Other",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2026-04-01",
            "status": "Active"
        }).insert(ignore_permissions=True)
        active_emps.append(e.name)
    frappe.db.commit()

print(f"Total employees for 55+ benchmark: {len(active_emps)}")

checkin_docs = []
for idx, emp_id in enumerate(active_emps[:55]):
    # vary times between 08:30 and 13:45
    minute = (idx * 5) % 300
    checkin_time = datetime.strptime(f"{test_date_50} 08:30:00", "%Y-%m-%d %H:%M:%S") + timedelta(minutes=minute)
    chk = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": emp_id,
        "time": checkin_time.strftime("%Y-%m-%d %H:%M:%S"),
        "log_type": "IN"
    })
    chk.insert(ignore_permissions=True)
    checkin_docs.append(chk)

frappe.db.commit()
print(f"Created {len(checkin_docs)} check-in records for {test_date_50}")

start_time = time.time()
daily_job(date=test_date_50)
elapsed = time.time() - start_time

logs_created = frappe.db.count("Late Arrival Log", {"attendance_date": test_date_50})
print(f"TC-8.3 (55 Checkins) PASS: Benchmark completed in {elapsed:.3f}s! Logs created: {logs_created}")
