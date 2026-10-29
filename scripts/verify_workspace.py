import frappe

frappe.connect()
frappe.set_user('Administrator')

ws = frappe.get_doc('Workspace', 'Attendance Policy')
print('Workspace:', ws.name)
print('Title:', ws.title)
print('Label:', ws.label)
print('')

print('Shortcuts:')
for s in ws.shortcuts:
    print('  -', s.label, '->', s.link_to)

print('\nLinks:')
for l in ws.links:
    if l.type == 'Card Break':
        print('\n  [CARD]', l.label)
    else:
        print('  -', l.label, '->', l.link_to, '(' + l.link_type + ')')

print('\nCharts:')
for c in ws.charts:
    print('  -', c.label, '->', c.chart_name)

print('\nDone!')