import frappe
frappe.connect()
frappe.set_user('Administrator')

print('Configuring Attendance Policy Settings...')

try:
    # Get or create settings
    if frappe.db.exists('Attendance Policy Settings', 'Attendance Policy Settings'):
        settings = frappe.get_doc('Attendance Policy Settings', 'Attendance Policy Settings')
        print('Settings document found')
    else:
        settings = frappe.new_doc('Attendance Policy Settings')
        print('Creating new settings document')
    
    # Configure company
    company = frappe.db.get_value('Company', {'company_name': 'Demo Company'}) or frappe.get_all('Company')[0].name if frappe.get_all('Company') else None
    if company:
        settings.company = company
        print(f'✓ Company set to: {company}')
    else:
        print('✗ Company not found')
    
    # Configure email recipient
    settings.email_recipient = 'admin@example.com'
    print(f'✓ Email recipient set to: admin@example.com')
    
    # Configure late grades
    settings.late_grade_1_6 = '1/6'  # 10 minutes late
    settings.late_grade_1_3 = '1/3'  # 20 minutes late  
    settings.late_grade_1_2 = '1/2'  # 30 minutes late
    settings.late_grade_full_day = 'Full Day'  # > 30 minutes late
    
    print(f'✓ Late grades configured:')
    print(f'   - 1/6 day deduction (10 min late)')
    print(f'   - 1/3 day deduction (20 min late)')
    print(f'   - 1/2 day deduction (30 min late)')
    print(f'   - Full day deduction (>30 min late)')
    
    # Set working hours (9 AM to 5 PM)
    settings.work_start_time = '09:00:00'
    settings.work_end_time = '17:00:00'
    print(f'✓ Working hours set: 9 AM to 5 PM')
    
    # Set late arrival window (8:30 AM to 9:00 AM)
    settings.arrival_window_start = '08:30:00'
    settings.arrival_window_end = '09:00:00'
    print(f'✓ Arrival window: 8:30 AM to 9:00 AM')
    
    # Save settings
    settings.save()
    frappe.db.commit()
    
    print('\n' + '=' * 50)
    print('SETTINGS CONFIGURED SUCCESSFULLY!')
    print('=' * 50)
    print('\nConfigured values:')
    print(f'  Company: {settings.company}')
    print(f'  Email: {settings.email_recipient}')
    print(f'  Late Grades: {settings.late_grade_1_6}, {settings.late_grade_1_3}, {settings.late_grade_1_2}, {settings.late_grade_full_day}')
    print(f'  Work Hours: {settings.work_start_time} to {settings.work_end_time}')
    print(f'  Arrival Window: {settings.arrival_window_start} to {settings.arrival_window_end}')
    
except Exception as e:
    print(f'\n✗ Error configuring settings: {e}')
    import traceback
    traceback.print_exc()