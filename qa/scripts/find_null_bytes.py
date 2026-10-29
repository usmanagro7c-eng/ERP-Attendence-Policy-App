import os
import pkgutil

os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='usman.local')
frappe.connect()

import attendance_policy

for _, name, _ in pkgutil.walk_packages(attendance_policy.__path__, 'attendance_policy.'):
    print("Checking:", name)
    try:
        __import__(name)
    except BaseException as e:
        print("FAILED on:", name, "with error:", type(e), e)
