import frappe
from frappe.utils import today, getdate, get_first_day, get_last_day

frappe.connect()
frappe.set_user('Administrator')

# 1. Ensure Company exists
company = frappe.db.get_value('Company', {'company_name': 'Demo Company'}) or (frappe.get_all('Company')[0].name if frappe.get_all('Company') else None)
if not company:
    # create simple company if missing (very minimal)
    company_doc = frappe.get_doc({
        'doctype': 'Company',
        'company_name': 'Demo Company',
        'company_abbr': 'DC',
        'default_currency': 'USD'
    })
    company_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    company = company_doc.name
    print('Created Company')
else:
    print('Company exists')

# 2. Create dummy active employees (if not exist)
employees = []
for i in range(1, 3):
    emp_name = f'Dummy Employee {i}'
    emp_id = frappe.db.get_value('Employee', {'employee_name': emp_name})
    if not emp_id:
        emp = frappe.get_doc({
            'doctype': 'Employee',
            'employee_name': emp_name,
            'status': 'Active',
            'company': company,
            'date_of_joining': today(),
            'naming_series': 'EMP-.YYYY.-'
        })
        emp.insert(ignore_permissions=True)
        frappe.db.commit()
        emp_id = emp.name
        print(f'Created employee: {emp_name}')
    else:
        print(f'Employee exists: {emp_name}')
    employees.append(emp_id)

# 3. Create dummy checkins for today (one on time, one late)
checkin_date = getdate(today())
from datetime import datetime, time as dtime

# clear any existing checkins for these employees today to avoid duplicates
frappe.db.sql("""
    DELETE FROM `tabEmployee Checkin`
    WHERE employee IN %s AND DATE(time) = %s
""", (tuple(employees), checkin_date))
frappe.db.commit()

# Employee 1: on time (08:45)
emp1 = employees[0]
checkin1_time = datetime.combine(checkin_date, dtime(hour=8, minute=45))
frappe.get_doc({
    'doctype': 'Employee Checkin',
    'employee': emp1,
    'time': checkin1_time,
    'log_type': 'IN'
}).insert(ignore_permissions=True)

# Employee 2: late (09:20) -> should be Grade 1 based on default settings (arrival_cutoff 09:00, grade1_end 10:00)
emp2 = employees[1]
checkin2_time = datetime.combine(checkin_date, dtime(hour=9, minute=20))
frappe.get_doc({
    'doctype': 'Employee Checkin',
    'employee': emp2,
    'time': checkin2_time,
    'log_type': 'IN'
}).insert(ignore_permissions=True)

frappe.db.commit()
print('Dummy checkins created')

# 4. Run daily job for today
try:
    from attendance_policy.tasks import daily_job
except ImportError:
    from attendance_policy.attendance_policy.tasks import daily_job
print('Running daily_job...')
daily_job(str(checkin_date))

# 5. Verify Late Arrival Log entries
logs = frappe.get_all('Late Arrival Log', fields=['name', 'employee', 'grade', 'deduction_days', 'status'])
print('Late Arrival Log entries after daily job:')
for l in logs:
    print(l)

# 6. Simulate month end: pick last day of current month
last_day = get_last_day(checkin_date)
# Ensure we have a pending Late Arrival Log for the month (already created)
try:
    from attendance_policy.tasks import month_end_job
except ImportError:
    from attendance_policy.attendance_policy.tasks import month_end_job
print('Running month_end_job for date:', last_day)
month_end_job(str(last_day))

# 7. Verify Late Deduction Entry and related docs
entries = frappe.get_all('Late Deduction Entry', fields=['name', 'employee', 'period_end', 'late_days', 'from_leave', 'from_salary'])
print('Late Deduction Entries:')
for e in entries:
    print(e)

# 8. Verify Additional Salary created (if any)
adds = frappe.get_all('Additional Salary', fields=['name', 'employee', 'salary_component', 'amount'])
print('Additional Salary records:')
for a in adds:
    print(a)

print('Test flow completed')
