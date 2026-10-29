import frappe

frappe.connect()
frappe.set_user('Administrator')

print('Creating/Updating Attendance Policy Workspace...')

# Delete if exists
if frappe.db.exists('Workspace', 'Attendance Policy'):
    frappe.db.delete('Workspace', 'Attendance Policy')
    print('Deleted old workspace')

# Create new workspace with proper structure
ws = frappe.new_doc('Workspace')
ws.name = 'Attendance Policy'
ws.label = 'Attendance Policy'
ws.title = 'Attendance Policy'
ws.icon = 'clock'
ws.module = 'Attendance Policy'
ws.is_hidden = 0
ws.public = 1

# Add shortcuts
ws.append('shortcuts', {
    'type': 'DocType',
    'label': 'Settings',
    'link_to': 'Attendance Policy Settings',
    'color': 'Grey'
})
ws.append('shortcuts', {
    'type': 'DocType',
    'label': 'Late Log',
    'link_to': 'Late Arrival Log',
    'doc_view': 'List',
    'color': 'Orange'
})
ws.append('shortcuts', {
    'type': 'DocType',
    'label': 'Deductions',
    'link_to': 'Late Deduction Entry',
    'doc_view': 'List',
    'color': 'Red'
})

# Add links with card breaks
ws.append('links', {'type': 'Card Break', 'label': 'Settings', 'hidden': 0})
ws.append('links', {
    'type': 'Link',
    'link_type': 'DocType',
    'link_to': 'Attendance Policy Settings',
    'label': 'Attendance Policy Settings',
    'hidden': 0
})

ws.append('links', {'type': 'Card Break', 'label': 'Tracking', 'hidden': 0})
ws.append('links', {
    'type': 'Link',
    'link_type': 'DocType',
    'link_to': 'Late Arrival Log',
    'label': 'Late Arrival Log',
    'hidden': 0
})
ws.append('links', {
    'type': 'Link',
    'link_type': 'DocType',
    'link_to': 'Late Deduction Entry',
    'label': 'Late Deduction Entry',
    'hidden': 0
})

ws.append('links', {'type': 'Card Break', 'label': 'Reports', 'hidden': 0})
ws.append('links', {
    'type': 'Link',
    'link_type': 'Report',
    'link_to': 'Daily Attendance Summary',
    'label': 'Daily Attendance Summary',
    'hidden': 0
})
ws.append('links', {
    'type': 'Link',
    'link_type': 'Report',
    'link_to': 'Habitual Late Comers',
    'label': 'Habitual Late Comers',
    'hidden': 0
})

# Add charts
ws.append('charts', {'chart_name': 'Late Arrivals by Grade', 'label': 'By Grade'})
ws.append('charts', {'chart_name': 'Late Arrivals by Employee', 'label': 'By Employee'})
ws.append('charts', {'chart_name': 'Late Arrivals Daily Trend', 'label': 'Trend'})

ws.insert(ignore_permissions=True)
frappe.db.commit()

print('✅ Workspace created successfully!')
print(f'   Shortcuts: {len(ws.shortcuts)}')
print(f'   Links/Cards: {len(ws.links)}')
print(f'   Charts: {len(ws.charts)}')
print('\\nAccess: http://localhost:8000/app/attendance-policy')