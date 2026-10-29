import frappe
frappe.connect()
frappe.set_user('Administrator')

print('=' * 80)
print('COMPREHENSIVE ATTENDANCE POLICY VERIFICATION')
print('=' * 80)

results = {
    'app_exists': False,
    'doctypes_created': False,
    'settings_configured': False,
    'charts_created': False,
    'workspace_exists': False,
    'reports_working': False,
    'jobs_exist': False,
    'leave_rules_configured': False,
    'shift_types_exist': False,
    'holiday_list_exists': False
}

issues = []

# 1. Check if app is installed
print('\n1. CHECKING APP INSTALLATION')
try:
    installed_apps = frappe.get_installed_apps()
    if 'attendance_policy' in installed_apps:
        print('   ✓ Attendance Policy app is installed')
        results['app_exists'] = True
    else:
        print('   ✗ Attendance Policy app is NOT installed')
        issues.append('App not installed')
except Exception as e:
    print(f'   ✗ Error checking app: {e}')
    issues.append(f'Error checking app: {e}')

# 2. Check DocTypes
print('\n2. CHECKING DOCTYPES')
doctypes_to_check = [
    'Attendance Policy Settings',
    'Late Arrival Log',
    'Late Deduction Entry'
]
created_doctypes = []

for dt in doctypes_to_check:
    try:
        if frappe.db.exists('DocType', dt):
            print(f'   ✓ {dt} exists')
            created_doctypes.append(dt)
        else:
            print(f'   ✗ {dt} does NOT exist')
            issues.append(f'DocType {dt} missing')
    except Exception as e:
        print(f'   ✗ Error checking {dt}: {e}')
        issues.append(f'Error checking DocType {dt}: {e}')

if len(created_doctypes) == len(doctypes_to_check):
    results['doctypes_created'] = True
    print(f'   ✓ All {len(doctypes_to_check)} DocTypes are created')

# 3. Check Settings configuration
print('\n3. CHECKING SETTINGS CONFIGURATION')
try:
    settings = frappe.get_single('Attendance Policy Settings')
    print(f'   ✓ Settings document exists')
    
    required_fields = {
        'company': 'Company configured',
        'email_recipient': 'Email recipient set',
        'late_grade_1_6': 'Late grade 1/6 configured',
        'late_grade_1_3': 'Late grade 1/3 configured',
        'late_grade_1_2': 'Late grade 1/2 configured',
        'late_grade_full_day': 'Full day late grade configured'
    }
    
    missing_fields = []
    for field, desc in required_fields.items():
        if not getattr(settings, field, None):
            missing_fields.append(field)
            print(f'   ✗ {desc} is missing')
    
    if not missing_fields:
        print(f'   ✓ All settings configured')
        results['settings_configured'] = True
    else:
        issues.append(f'Missing settings fields: {missing_fields}')
except Exception as e:
    print(f'   ✗ Error checking settings: {e}')
    issues.append(f'Error checking settings: {e}')

# 4. Check Dashboard Charts
print('\n4. CHECKING DASHBOARD CHARTS')
expected_charts = [
    'Late Arrivals by Grade',
    'Late Arrivals by Employee',
    'Late Arrivals Daily Trend'
]

charts_found = []
try:
    charts = frappe.get_all('Dashboard Chart', 
        filters={'module': 'Attendance Policy'},
        fields=['name', 'chart_name', 'chart_type', 'disabled'])
    
    for chart in charts:
        if chart.chart_name in expected_charts:
            charts_found.append(chart.chart_name)
            status = '✓' if not chart.disabled else '✗'
            print(f'   {status} {chart.chart_name} ({chart.chart_type})')
    
    missing_charts = set(expected_charts) - set(charts_found)
    for missing in missing_charts:
        print(f'   ✗ Missing: {missing}')
        issues.append(f'Missing chart: {missing}')
    
    if len(charts_found) == len(expected_charts):
        results['charts_created'] = True
        print(f'   ✓ All {len(expected_charts)} charts created')
        
except Exception as e:
    print(f'   ✗ Error checking charts: {e}')
    issues.append(f'Error checking charts: {e}')

# 5. Check Workspace
print('\n5. CHECKING WORKSPACE')
try:
    workspace = frappe.get_doc('Workspace', 'Attendance Policy')
    print(f'   ✓ Workspace exists')
    
    if workspace.charts:
        print(f'   ✓ Has {len(workspace.charts)} charts linked')
        results['workspace_exists'] = True
    else:
        print(f'   ✗ No charts linked to workspace')
        issues.append('No charts in workspace')
        
    if workspace.cards:
        print(f'   ✓ Has {len(workspace.cards)} cards')
    else:
        print(f'   ✗ No cards in workspace')
        
except Exception as e:
    print(f'   ✗ Error checking workspace: {e}')
    issues.append(f'Error checking workspace: {e}')

# 6. Check Reports
print('\n6. CHECKING REPORTS')
reports_to_check = [
    'Daily Attendance Summary',
    'Habitual Late Comers'
]

reports_working = []
for report in reports_to_check:
    try:
        # Try to get report definition
        report_def = frappe.get_doc('Report', report)
        print(f'   ✓ {report} report exists')
        
        # Check if the Python file exists
        module_path = frappe.get_module_path('attendance_policy')
        report_path = f"{module_path}/report/{report.lower().replace(' ', '_')}/{report.lower().replace(' ', '_')}.py"
        
        import os
        if os.path.exists(report_path):
            print(f'   ✓ {report} Python file exists')
            reports_working.append(report)
        else:
            print(f'   ✗ {report} Python file missing: {report_path}')
            issues.append(f'Report {report} Python file missing')
            
    except Exception as e:
        print(f'   ✗ Error checking report {report}: {e}')
        issues.append(f'Error checking report {report}: {e}')

if len(reports_working) == len(reports_to_check):
    results['reports_working'] = True
    print(f'   ✓ All {len(reports_to_check)} reports are configured')

# 7. Check Scheduled Jobs
print('\n7. CHECKING SCHEDULED JOBS')
jobs_to_check = [
    'attendance_policy.attendance_policy.tasks.daily_late_arrival_check',
    'attendance_policy.attendance_policy.tasks.month_end_deduction'
]

jobs_found = []
try:
    all_jobs = frappe.get_all('Scheduled Job Type',
        filters={'enabled': 1},
        fields=['method', 'frequency'])
    
    for job in all_jobs:
        if job.method in jobs_to_check:
            jobs_found.append(job.method)
            print(f'   ✓ {job.method} ({job.frequency})')
    
    missing_jobs = set(jobs_to_check) - set(jobs_found)
    for missing in missing_jobs:
        print(f'   ✗ Missing job: {missing}')
        issues.append(f'Missing scheduled job: {missing}')
    
    if len(jobs_found) == len(jobs_to_check):
        results['jobs_exist'] = True
        print(f'   ✓ All {len(jobs_to_check)} scheduled jobs configured')
        
except Exception as e:
    print(f'   ✗ Error checking jobs: {e}')
    issues.append(f'Error checking jobs: {e}')

# 8. Check Leave Rules
print('\n8. CHECKING LEAVE RULES')
try:
    # Check if leave types exist
    leave_types = frappe.get_all('Leave Type',
        filters={'name': ['in', ['Casual Leave', 'Annual Leave']]},
        fields=['name', 'max_continuous_days_allowed', 'max_days_allowed'])
    
    for lt in leave_types:
        print(f'   ✓ {lt.name} exists')
        if lt.name == 'Casual Leave':
            if lt.max_continuous_days_allowed == 3:
                print(f'   ✓ Casual Leave max consecutive days = 3')
            else:
                print(f'   ✗ Casual Leave max consecutive days ≠ 3 (is {lt.max_continuous_days_allowed})')
                issues.append('Casual Leave max consecutive days not 3')
    
    if len(leave_types) >= 2:
        results['leave_rules_configured'] = True
        print(f'   ✓ Both leave types configured')
    else:
        print(f'   ✗ Missing leave types')
        issues.append('Missing leave types')
        
except Exception as e:
    print(f'   ✗ Error checking leave rules: {e}')
    issues.append(f'Error checking leave rules: {e}')

# 9. Check Shift Types
print('\n9. CHECKING SHIFT TYPES')
try:
    shift_types = frappe.get_all('Shift Type',
        fields=['name', 'start_time', 'end_time'])
    
    print(f'   ✓ Found {len(shift_types)} shift types')
    results['shift_types_exist'] = True
    
except Exception as e:
    print(f'   ✗ Error checking shift types: {e}')
    issues.append(f'Error checking shift types: {e}')

# 10. Check Holiday List
print('\n10. CHECKING HOLIDAY LIST')
try:
    holiday_lists = frappe.get_all('Holiday List',
        fields=['name', 'total_holidays'])
    
    for hl in holiday_lists:
        print(f'   ✓ {hl.name} ({hl.total_holidays} holidays)')
    
    if holiday_lists:
        results['holiday_list_exists'] = True
        print(f'   ✓ Holiday list exists')
    else:
        print(f'   ✗ No holiday list found')
        issues.append('No holiday list found')
        
except Exception as e:
    print(f'   ✗ Error checking holiday list: {e}')
    issues.append(f'Error checking holiday list: {e}')

# Summary
print('\n' + '=' * 80)
print('VERIFICATION SUMMARY')
print('=' * 80)

success_count = sum(1 for v in results.values() if v)
total_count = len(results)

print(f'\nSuccess: {success_count}/{total_count}')
print(f'Issues found: {len(issues)}')

if issues:
    print('\nISSUES:')
    for i, issue in enumerate(issues, 1):
        print(f'  {i}. {issue}')
else:
    print('\n✓ All checks passed!')

print('\n' + '-' * 80)
print('RECOMMENDATIONS:')
if success_count == total_count:
    print('1. All systems operational ✅')
    print('2. Test daily email at 9 PM UTC tonight')
    print('3. Test month-end deduction on last day of month')
else:
    print('1. Address the issues listed above')
    print('2. Fix missing components before testing')
    print('3. Clear browser cache after fixing issues')

print('=' * 80)