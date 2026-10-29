import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from attendance_policy.tasks import is_holiday
from hrms.utils.holiday_list import get_holiday_list_for_employee

frappe.init(site='erp.local')
frappe.connect()

emp1 = frappe.db.get_value('Employee', {'first_name': 'QA_E1'})
print("get_holiday_list_for_employee:", get_holiday_list_for_employee(emp1, raise_exception=False))
print("is_holiday 2026-11-01:", is_holiday(emp1, "2026-11-01"))
print("Holiday exists in QA_HL for 2026-11-01:", frappe.db.exists("Holiday", {"parent": "QA_HL", "holiday_date": "2026-11-01"}))
