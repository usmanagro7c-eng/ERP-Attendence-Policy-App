import frappe
frappe.connect()
frappe.set_user('Administrator')

print('Checking current settings state...')

try:
    # Check if settings exist
    if frappe.db.exists('Attendance Policy Settings', 'Attendance Policy Settings'):
        settings = frappe.get_doc('Attendance Policy Settings', 'Attendance Policy Settings')
        print('Settings document exists')
        print(f'Company: {settings.company or "NOT SET"}')
        print(f'Email: {settings.email_recipient or "NOT SET"}')
        print(f'Late Grade 1/6: {settings.late_grade_1_6 or "NOT SET"}')
        print(f'Late Grade 1/3: {settings.late_grade_1_3 or "NOT SET"}')
        print(f'Late Grade 1/2: {settings.late_grade_1_2 or "NOT SET"}')
        print(f'Late Grade Full: {settings.late_grade_full_day or "NOT SET"}')
    else:
        print('Settings document does NOT exist - will create')
        
        # Create settings
        settings = frappe.new_doc('Attendance Policy Settings')
        settings.company = 'Demo Company'
        settings.email_recipient = 'admin@example.com'
        settings.late_grade_1_6 = '1/6'
        settings.late_grade_1_3 = '1/3'
        settings.late_grade_1_2 = '1/2'
        settings.late_grade_full_day = 'Full Day'
        settings.work_start_time = '09:00:00'
        settings.work_end_time = '17:00:00'
        settings.arrival_window_start = '08:30:00'
        settings.arrival_window_end = '09:00:00'
        
        settings.save()
        frappe.db.commit()
        
        print('\n✓ Settings created and configured!')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
