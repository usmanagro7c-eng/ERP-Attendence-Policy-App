import frappe
frappe.connect()
frappe.set_user('Administrator')

meta = frappe.get_meta('Workspace')
print('Workspace DocType Fields:')
print()
for field in meta.fields:
    if field.fieldtype in ['Select', 'Link', 'Data']:
        print(f'{field.fieldname} ({field.fieldtype}): {field.label}')
        if field.fieldtype == 'Select' and field.options:
            print(f'  Options: {field.options[:200]}...')