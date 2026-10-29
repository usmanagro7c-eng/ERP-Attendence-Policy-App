import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='usman.local')
frappe.connect()

try:
    from frappe.tests.utils import FrappeTestCase
    print("Found FrappeTestCase:", FrappeTestCase)
except ImportError as e:
    print("FrappeTestCase error:", e)

try:
    from frappe.tests import IntegrationTestCase
    print("Found IntegrationTestCase:", IntegrationTestCase)
except ImportError as e:
    print("IntegrationTestCase error:", e)
