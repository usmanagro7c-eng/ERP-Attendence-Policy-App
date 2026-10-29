import os, sys
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from datetime import datetime, time
from frappe.utils import getdate

frappe.init(site='erp.local')
frappe.connect()

company = 'Demo Company'
test_date = getdate('2026-10-21')

# Clean existing checkins and logs for 2026-10-21
for c in frappe.get_all('Employee Checkin', filters={'time': ['between', ['2026-10-21 00:00:00', '2026-10-21 23:59:59']]}):
    frappe.delete_doc('Employee Checkin', c.name, force=True)

for l in frappe.get_all('Late Arrival Log', filters={'attendance_date': test_date}):
    frappe.delete_doc('Late Arrival Log', l.name, force=True)

frappe.db.commit()

# Create BM employees 01 to 12 and QA_BM_LEAVE
bm_emps = [f'QA_BM_{i:02d}' for i in range(1, 13)] + ['QA_BM_LEAVE']
for ename in bm_emps:
    if not frappe.db.get_value('Employee', {'first_name': ename}):
        emp = frappe.new_doc('Employee')
        emp.first_name = ename
        emp.company = company
        emp.status = 'Active'
        emp.date_of_joining = '2025-01-01'
        emp.date_of_birth = '1990-01-01'
        emp.gender = 'Male'
        emp.holiday_list = 'QA_HL'
        emp.insert(ignore_permissions=True)
        frappe.db.commit()

# Create approved leave for QA_BM_LEAVE on 2026-10-21
emp_leave_id = frappe.db.get_value('Employee', {'first_name': 'QA_BM_LEAVE'})
if not frappe.db.exists('Leave Allocation', {'employee': emp_leave_id, 'leave_type': 'Casual Leave', 'docstatus': 1}):
    la = frappe.new_doc('Leave Allocation')
    la.employee = emp_leave_id
    la.leave_type = 'Casual Leave'
    la.from_date = '2026-07-01'
    la.to_date = '2027-06-30'
    la.new_leaves_allocated = 10
    la.insert(ignore_permissions=True)
    la.submit()
    frappe.db.commit()

for la_old in frappe.get_all('Leave Application', filters={'employee': emp_leave_id, 'from_date': test_date}):
    frappe.delete_doc('Leave Application', la_old.name, force=True)

frappe.db.commit()
lapp = frappe.new_doc('Leave Application')
lapp.employee = emp_leave_id
lapp.leave_type = 'Casual Leave'
lapp.from_date = test_date
lapp.to_date = test_date
lapp.description = 'Medical checkup'
lapp.leave_approver = 'admin@example.com'
lapp.status = 'Approved'
lapp.insert(ignore_permissions=True)
lapp.submit()
frappe.db.commit()

# Times for BM 01 to 10
matrix = [
    ('QA_BM_01', (8, 30, 0), (17, 30, 0)),
    ('QA_BM_02', (9, 0, 0), (17, 30, 0)),
    ('QA_BM_03', (9, 0, 1), (17, 30, 0)),
    ('QA_BM_04', (10, 0, 0), (17, 30, 0)),
    ('QA_BM_05', (10, 0, 1), (17, 30, 0)),
    ('QA_BM_06', (11, 0, 0), (17, 30, 0)),
    ('QA_BM_07', (11, 0, 1), (17, 30, 0)),
    ('QA_BM_08', (13, 29, 59), (17, 30, 0)),
    ('QA_BM_09', (13, 30, 0), (17, 30, 0)),
    ('QA_BM_10', (15, 0, 0), (17, 30, 0)),
]

for ename, in_t, out_t in matrix:
    eid = frappe.db.get_value('Employee', {'first_name': ename})
    t_in = datetime.combine(test_date, time(*in_t))
    t_out = datetime.combine(test_date, time(*out_t))
    frappe.get_doc({'doctype': 'Employee Checkin', 'employee': eid, 'time': t_in, 'log_type': 'IN'}).insert(ignore_permissions=True)
    frappe.get_doc({'doctype': 'Employee Checkin', 'employee': eid, 'time': t_out, 'log_type': 'OUT'}).insert(ignore_permissions=True)

# TC-3.1: Single checkin QA_BM_11 (09:30:00, no exit)
eid_11 = frappe.db.get_value('Employee', {'first_name': 'QA_BM_11'})
frappe.get_doc({'doctype': 'Employee Checkin', 'employee': eid_11, 'time': datetime.combine(test_date, time(9, 30, 0)), 'log_type': 'IN'}).insert(ignore_permissions=True)

# TC-3.2: Multiple checkins QA_BM_12
eid_12 = frappe.db.get_value('Employee', {'first_name': 'QA_BM_12'})
for t in [(9, 15, 0), (11, 30, 0), (14, 0, 0), (17, 30, 0)]:
    frappe.get_doc({'doctype': 'Employee Checkin', 'employee': eid_12, 'time': datetime.combine(test_date, time(*t)), 'log_type': 'IN'}).insert(ignore_permissions=True)

# TC-3.4: QA_BM_LEAVE checkin at 10:00:00
frappe.get_doc({'doctype': 'Employee Checkin', 'employee': emp_leave_id, 'time': datetime.combine(test_date, time(10, 0, 0)), 'log_type': 'IN'}).insert(ignore_permissions=True)

# TC-3.6: QA_INACTIVE checkin at 10:00:00
eid_inact = frappe.db.get_value('Employee', {'first_name': 'QA_INACTIVE'})
frappe.get_doc({'doctype': 'Employee Checkin', 'employee': eid_inact, 'time': datetime.combine(test_date, time(10, 0, 0)), 'log_type': 'IN'}).insert(ignore_permissions=True)

# TC-3.5: Checkin on Sunday 2026-10-18 (holiday)
eid_01 = frappe.db.get_value('Employee', {'first_name': 'QA_BM_01'})
for c_old in frappe.get_all('Employee Checkin', filters={'time': ['between', ['2026-10-18 00:00:00', '2026-10-18 23:59:59']]}):
    frappe.delete_doc('Employee Checkin', c_old.name, force=True)
frappe.get_doc({'doctype': 'Employee Checkin', 'employee': eid_01, 'time': datetime(2026, 10, 18, 10, 0, 0), 'log_type': 'IN'}).insert(ignore_permissions=True)

frappe.db.commit()
print('Checkins setup complete for 2026-10-21 and 2026-10-18')
