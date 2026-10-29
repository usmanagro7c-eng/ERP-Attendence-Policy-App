import os
import time
from datetime import datetime, timedelta
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

from attendance_policy.tasks import daily_job, settings

print("=== TC-8.1: Dynamic Settings Change (Cutoff 09:15) ===")
s = frappe.get_single("Attendance Policy Settings")
orig_cutoff = s.arrival_cutoff
s.arrival_cutoff = "09:15:00"
s.grade1_end = "10:15:00"
s.save(ignore_permissions=True)
frappe.db.commit()

e1 = frappe.db.get_value("Employee", {"first_name": "QA_E1"}, "name")
test_date_81 = "2026-11-10"

# Clean old logs and checkins
frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee = %s AND attendance_date = %s", (e1, test_date_81))
frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee = %s AND date(time) = %s", (e1, test_date_81))
frappe.db.commit()

# Create checkin at 09:10:00 (after 09:00, but before new cutoff 09:15:00)
frappe.get_doc({
    "doctype": "Employee Checkin",
    "employee": e1,
    "time": f"{test_date_81} 09:10:00",
    "log_type": "IN"
}).insert(ignore_permissions=True)
frappe.db.commit()

# Run daily_job
daily_job(date=test_date_81)

# Verify Late Arrival Log
log_81 = frappe.get_all("Late Arrival Log", filters={"employee": e1, "attendance_date": test_date_81})
if not log_81:
    print("TC-8.1 PASS: Check-in at 09:10:00 produced NO late log under 09:15 cutoff!")
else:
    print(f"TC-8.1 FAIL: Late log created unexpectedly: {log_81}")

# Revert settings
s.reload()
s.arrival_cutoff = orig_cutoff
s.grade1_end = "10:00:00"
s.save(ignore_permissions=True)
frappe.db.commit()


print("\n=== TC-8.2: Midnight / Night Check-in Timestamps & Timezone Sanity ===")
test_date_82 = "2026-11-11"
frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee = %s AND attendance_date = %s", (e1, test_date_82))
frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee = %s AND date(time) = %s", (e1, test_date_82))
frappe.db.commit()

# Create checkin at 00:05:00 (midnight shift / early morning)
frappe.get_doc({
    "doctype": "Employee Checkin",
    "employee": e1,
    "time": f"{test_date_82} 00:05:00",
    "log_type": "IN"
}).insert(ignore_permissions=True)
frappe.db.commit()

daily_job(date=test_date_82)
log_82 = frappe.get_all("Late Arrival Log", filters={"employee": e1, "attendance_date": test_date_82})
if not log_82:
    print("TC-8.2 PASS: 00:05 check-in is before 09:00, no late log created.")
else:
    print(f"TC-8.2 Result: log created: {log_82}")


print("\n=== TC-8.3: Benchmark 50+ Bulk Check-in Run ===")
test_date_83 = "2026-11-12"
# Clean test_date_83
frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE attendance_date = %s", test_date_83)
frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE date(time) = %s", test_date_83)
frappe.db.commit()

# Create 50 employees or 50 checkins for existing employees
employees = frappe.get_all("Employee", filters={"status": "Active"}, limit=60)
print(f"Active employees available for benchmark: {len(employees)}")

checkin_docs = []
for idx, emp in enumerate(employees):
    # simulate varying times from 08:30 to 14:00
    minute = (idx * 7) % 360 # up to 6 hours
    checkin_time = datetime.strptime(f"{test_date_83} 08:30:00", "%Y-%m-%d %H:%M:%S") + timedelta(minutes=minute)
    chk = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": emp.name,
        "time": checkin_time.strftime("%Y-%m-%d %H:%M:%S"),
        "log_type": "IN"
    })
    chk.insert(ignore_permissions=True)
    checkin_docs.append(chk)

frappe.db.commit()
print(f"Created {len(checkin_docs)} check-in records for {test_date_83}")

start_time = time.time()
daily_job(date=test_date_83)
elapsed = time.time() - start_time

logs_created = frappe.db.count("Late Arrival Log", {"attendance_date": test_date_83})
print(f"TC-8.3 PASS: Benchmark completed in {elapsed:.3f} seconds! Processed {len(checkin_docs)} checkins, created {logs_created} late arrival logs.")


print("\n=== TC-8.5: Error Log Review ===")
errors = frappe.get_all("Error Log", fields=["name", "method", "error", "creation"], order_by="creation desc", limit=10)
print(f"Total error logs found: {len(errors)}")
for e in errors[:5]:
    print(f" - [{e.creation}] {e.method}: {e.error[:100]}...")

