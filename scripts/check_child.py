import frappe
frappe.connect()
frappe.set_user('Administrator')

# Get workspace link child table fields
link_meta = frappe.get_meta('Workspace Link')
print('Workspace Link fields:')
for f in link_meta.fields:
    print(f'  {f.fieldname}: {f.fieldtype}')

print('')

# Get workspace chart child table fields
chart_meta = frappe.get_meta('Workspace Chart')
print('Workspace Chart fields:')
for f in chart_meta.fields:
    print(f'  {f.fieldname}: {f.fieldtype}')

print('')
print('Done')