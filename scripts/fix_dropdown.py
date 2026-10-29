import frappe
frappe.connect()
frappe.set_user('Administrator')

print('=== Reloading metadata for Workspace and Dashboard ===')

# Clear specific metadata cache
frappe.clear_cache(doctype='Workspace')
frappe.clear_cache(doctype='Dashboard Chart')
frappe.clear_cache(doctype='Workspace Chart')
frappe.clear_cache(doctype='Workspace Link')

# Force reload metadata
frappe.get_meta('Workspace', cached=False)
frappe.get_meta('Dashboard Chart', cached=False)
frappe.get_meta('Workspace Chart', cached=False)
frappe.get_meta('Workspace Link', cached=False)

print('Metadata cleared and reloaded')

# Verify our charts are accessible
print('\n=== Verifying Dashboard Charts ===')
charts = frappe.get_all('Dashboard Chart', 
    filters={'module': 'Attendance Policy'},
    fields=['name', 'chart_name'])
    
for c in charts:
    print(f'  ✓ {c.name}')

# Check if Link field has proper options
print('\n=== Checking Workspace Chart Link field ===')
meta = frappe.get_meta('Workspace Chart')
chart_name_field = meta.get_field('chart_name')
print(f'Field: {chart_name_field.fieldname}')
print(f'Type: {chart_name_field.fieldtype}')
print(f'Options: {chart_name_field.options}')

print('\n=== Rebuilding website cache ===')
frappe.db.commit()

print('\nDone! Please do the following:')
print('1. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)')
print('2. Or clear browser cache and reload')
print('3. Try opening Workspace editor again')
