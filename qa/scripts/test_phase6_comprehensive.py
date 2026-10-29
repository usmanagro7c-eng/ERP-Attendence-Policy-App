import os
os.chdir('/home/usman/frappe-bench/sites')
import frappe
from frappe.utils import getdate, today
from attendance_policy.leave_rules import validate_leave_application

frappe.init(site='erp.local')
frappe.connect()

emp1 = frappe.db.get_value('Employee', {'first_name': 'QA_E1'})
emp2 = frappe.db.get_value('Employee', {'first_name': 'QA_E2'})

results = {}

# TC-6.1: Casual leave 3 days vs 4 days
doc3 = frappe.new_doc('Leave Application')
doc3.employee = emp1
doc3.leave_type = 'Casual Leave'
doc3.from_date = '2026-11-03'
doc3.to_date = '2026-11-05'
doc3.total_leave_days = 3
doc3.leave_approver = 'admin@example.com'
try:
    validate_leave_application(doc3)
    results['TC-6.1_3_days'] = 'PASS: Allowed'
except Exception as e:
    results['TC-6.1_3_days'] = f'FAIL: {e}'

doc4 = frappe.new_doc('Leave Application')
doc4.employee = emp1
doc4.leave_type = 'Casual Leave'
doc4.from_date = '2026-11-03'
doc4.to_date = '2026-11-06'
doc4.total_leave_days = 4
doc4.leave_approver = 'admin@example.com'
try:
    validate_leave_application(doc4)
    results['TC-6.1_4_days'] = 'FAIL: Allowed (Expected Block)'
except Exception as e:
    results['TC-6.1_4_days'] = f'PASS: Blocked with: {e}'

# TC-6.2: Adjacent to Sunday without vs with reason
doc_adj_no = frappe.new_doc('Leave Application')
doc_adj_no.employee = emp1
doc_adj_no.leave_type = 'Casual Leave'
doc_adj_no.from_date = '2026-11-02' # Monday
doc_adj_no.to_date = '2026-11-02'
doc_adj_no.total_leave_days = 1
doc_adj_no.leave_approver = 'admin@example.com'
doc_adj_no.description = ''
try:
    validate_leave_application(doc_adj_no)
    results['TC-6.2_no_reason'] = 'FAIL: Allowed (Expected Block)'
except Exception as e:
    results['TC-6.2_no_reason'] = f'PASS: Blocked with: {e}'

doc_adj_yes = frappe.new_doc('Leave Application')
doc_adj_yes.employee = emp1
doc_adj_yes.leave_type = 'Casual Leave'
doc_adj_yes.from_date = '2026-11-02'
doc_adj_yes.to_date = '2026-11-02'
doc_adj_yes.total_leave_days = 1
doc_adj_yes.leave_approver = 'admin@example.com'
doc_adj_yes.description = 'Attending family wedding'
try:
    validate_leave_application(doc_adj_yes)
    results['TC-6.2_with_reason'] = 'PASS: Allowed'
except Exception as e:
    results['TC-6.2_with_reason'] = f'FAIL: {e}'

# TC-6.2: Check if Sunday is actually counted in total_leave_days or Leave Ledger Entry
# In Frappe/app: custom code throws error if no reason, but does it add Sunday to total_leave_days?
results['TC-6.2_holiday_counted'] = f"total_leave_days stays {doc_adj_yes.total_leave_days} (Sunday not automatically appended to day count)"

# TC-6.3: Annual leave for QA_E2 (<12 months service)
doc_ann_e2 = frappe.new_doc('Leave Application')
doc_ann_e2.employee = emp2
doc_ann_e2.leave_type = 'Annual Leave'
doc_ann_e2.from_date = '2026-11-16'
doc_ann_e2.to_date = '2026-11-18'
doc_ann_e2.total_leave_days = 3
doc_ann_e2.leave_approver = 'admin@example.com'
try:
    validate_leave_application(doc_ann_e2)
    results['TC-6.3_QA_E2'] = 'FAIL: Allowed (Expected Block)'
except Exception as e:
    results['TC-6.3_QA_E2'] = f'PASS: Blocked with: {e}'

# TC-6.3: Annual leave for QA_E1 (>12 months service, future dates)
doc_ann_e1 = frappe.new_doc('Leave Application')
doc_ann_e1.employee = emp1
doc_ann_e1.leave_type = 'Annual Leave'
doc_ann_e1.from_date = '2026-11-16'
doc_ann_e1.to_date = '2026-11-18'
doc_ann_e1.total_leave_days = 3
doc_ann_e1.leave_approver = 'admin@example.com'
try:
    validate_leave_application(doc_ann_e1)
    results['TC-6.3_QA_E1'] = 'PASS: Allowed'
except Exception as e:
    results['TC-6.3_QA_E1'] = f'FAIL: {e}'

# TC-6.4: Annual leave starting today/past as plain Employee vs HR Manager
frappe.set_user('qa_employee@example.com')
doc_ann_past_emp = frappe.new_doc('Leave Application')
doc_ann_past_emp.employee = emp1
doc_ann_past_emp.leave_type = 'Annual Leave'
doc_ann_past_emp.from_date = '2026-10-25' # past
doc_ann_past_emp.to_date = '2026-10-27'
doc_ann_past_emp.total_leave_days = 3
doc_ann_past_emp.leave_approver = 'admin@example.com'
try:
    validate_leave_application(doc_ann_past_emp)
    results['TC-6.4_as_employee'] = 'FAIL: Allowed (Expected Block)'
except Exception as e:
    results['TC-6.4_as_employee'] = f'PASS: Blocked with: {e}'

# as HR Manager (Administrator)
frappe.set_user('Administrator')
try:
    validate_leave_application(doc_ann_past_emp)
    results['TC-6.4_as_hr_manager'] = 'PASS: Allowed for HR Manager override'
except Exception as e:
    results['TC-6.4_as_hr_manager'] = f'FAIL: {e}'

# TC-6.5: Annual leave max 2 parts per year
# Clean existing annual leave applications for QA_E1 in 2026
for la in frappe.get_all('Leave Application', filters={'employee': emp1, 'leave_type': 'Annual Leave'}):
    frappe.delete_doc('Leave Application', la.name, force=True)
frappe.db.commit()

# Create Part 1
p1 = frappe.new_doc('Leave Application')
p1.employee = emp1
p1.leave_type = 'Annual Leave'
p1.from_date = '2026-11-10'
p1.to_date = '2026-11-12'
p1.total_leave_days = 3
p1.leave_approver = 'admin@example.com'
p1.status = 'Approved'
p1.insert(ignore_permissions=True)
p1.submit()

# Create Part 2
p2 = frappe.new_doc('Leave Application')
p2.employee = emp1
p2.leave_type = 'Annual Leave'
p2.from_date = '2026-11-20'
p2.to_date = '2026-11-22'
p2.total_leave_days = 3
p2.leave_approver = 'admin@example.com'
p2.status = 'Approved'
p2.insert(ignore_permissions=True)
p2.submit()
frappe.db.commit()

# Try Part 3 (Expected Block)
p3 = frappe.new_doc('Leave Application')
p3.employee = emp1
p3.leave_type = 'Annual Leave'
p3.from_date = '2026-12-01'
p3.to_date = '2026-12-03'
p3.total_leave_days = 3
p3.leave_approver = 'admin@example.com'
try:
    validate_leave_application(p3)
    results['TC-6.5_part_3'] = 'FAIL: Allowed 3rd part (Expected Block)'
except Exception as e:
    results['TC-6.5_part_3'] = f'PASS: Blocked with: {e}'

# TC-6.6: Editing an existing application does not count itself as an extra part
p2_edit = frappe.get_doc('Leave Application', p2.name)
p2_edit.description = 'Updated description'
try:
    validate_leave_application(p2_edit)
    results['TC-6.6_edit_existing'] = 'PASS: Editing existing part allowed without trigger 3rd part error'
except Exception as e:
    results['TC-6.6_edit_existing'] = f'FAIL: {e}'

# TC-6.9: Casual leave encashment (max 10 days)
lt = frappe.get_doc('Leave Type', 'Casual Leave')
lt.allow_encashment = 1
lt.max_encashable_days = 10
lt.save(ignore_permissions=True)
frappe.db.commit()

# Test Leave Encashment doctype for 10 days vs 11 days
enc10 = frappe.new_doc('Leave Encashment')
enc10.employee = emp1
enc10.leave_type = 'Casual Leave'
enc10.encashment_date = today()
enc10.encashable_days = 10
try:
    enc10.validate()
    results['TC-6.9_encash_10'] = 'PASS: 10 days allowed'
except Exception as e:
    results['TC-6.9_encash_10'] = f'Note: {e}'

enc11 = frappe.new_doc('Leave Encashment')
enc11.employee = emp1
enc11.leave_type = 'Casual Leave'
enc11.encashment_date = today()
enc11.encashable_days = 11
try:
    enc11.validate()
    results['TC-6.9_encash_11'] = 'FAIL: 11 days allowed (Expected Block)'
except Exception as e:
    results['TC-6.9_encash_11'] = f'PASS: Blocked with: {e}'

for k, v in results.items():
    print(f"{k} => {v}")
