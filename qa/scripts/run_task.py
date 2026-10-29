import sys, os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='erp.local')
frappe.connect()

func = sys.argv[1]
args = sys.argv[2:]
mod_name, fn_name = func.rsplit('.', 1)
mod = __import__(mod_name, fromlist=[fn_name])
fn = getattr(mod, fn_name)
res = fn(*args)
print("TASK_RESULT:", res)
frappe.db.commit()
