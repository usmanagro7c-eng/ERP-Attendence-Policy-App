import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
frappe.init(site='usman.local')
frappe.connect()

for dt in ['Number Card']:
    meta = frappe.get_meta(dt)
    reqd = [f.fieldname for f in meta.fields if f.reqd]
    all_f = [f.fieldname for f in meta.fields if f.fieldname]
    print(f"\n--- {dt} ---")
    print("Reqd:", reqd)
    print("Fields:", all_f)
