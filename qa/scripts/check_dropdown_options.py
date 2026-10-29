import frappe
frappe.connect()
frappe.set_user('Administrator')

# Check available Dashboard Charts
print('=== Available Dashboard Charts ===')
charts = frappe.get_all('Dashboard Chart', fields=['name', 'chart_name', 'chart_type'])
for c in charts:
    print(f"  {c.name} - {c.chart_name} ({c.chart_type})")

print('\n=== Our Attendance Policy Charts ===')
our_charts = frappe.get_all('Dashboard Chart', 
    filters={'module': 'Attendance Policy'},
    fields=['name', 'chart_name', 'chart_type'])
for c in our_charts:
    print(f"  {c.name} - {c.chart_name} ({c.chart_type})")

print('\n=== Workspace Configuration ===')
workspace = frappe.get_doc('Workspace', 'Attendance Policy')
print(f"Title: {workspace.title}")
print(f"Module: {workspace.module}")
print(f"Charts in workspace: {len(workspace.charts)}")
for chart in workspace.charts:
    print(f"  - Chart: {chart.chart_name}, Label: {chart.label}")

print('\n=== Checking Metadata Cache ===')
print(f"Workspace Chart meta loaded: {frappe.cache().get('meta_Workspace Chart') is not None}")
print(f"Dashboard Chart meta loaded: {frappe.cache().get('meta_Dashboard Chart') is not None}")

print('\nDone')
