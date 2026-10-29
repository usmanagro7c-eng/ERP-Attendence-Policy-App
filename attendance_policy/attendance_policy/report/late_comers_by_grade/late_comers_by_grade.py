import frappe
from frappe import _
from frappe.utils import get_first_day, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	from_date = filters.from_date or get_first_day(today())
	to_date = filters.to_date or today()

	conditions = ["attendance_date between %(from_date)s and %(to_date)s"]
	values = {"from_date": from_date, "to_date": to_date}

	if filters.employee:
		conditions.append("employee = %(employee)s")
		values["employee"] = filters.employee

	if filters.department:
		conditions.append("department = %(department)s")
		values["department"] = filters.department

	where_clause = " and ".join(conditions)

	# Group by employee, counting by grade and collecting distinct dates
	data = frappe.db.sql(
		f"""
		select
			employee,
			employee_name,
			department,
			sum(grade = 'Grade 1') as g1,
			sum(grade = 'Grade 2') as g2,
			sum(grade = 'Grade 3') as g3,
			count(*) as total,
			group_concat(distinct date_format(attendance_date, '%%d %%b') order by attendance_date separator ', ') as dates
		from `tabLate Arrival Log`
		where {where_clause}
		group by employee, employee_name, department
		order by total desc, employee_name asc
		""",
		values,
		as_dict=True,
	)

	columns = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Grade 1"), "fieldname": "g1", "fieldtype": "Int", "width": 90},
		{"label": _("Grade 2"), "fieldname": "g2", "fieldtype": "Int", "width": 90},
		{"label": _("Grade 3"), "fieldname": "g3", "fieldtype": "Int", "width": 90},
		{"label": _("Total Late"), "fieldname": "total", "fieldtype": "Int", "width": 100},
		{"label": _("Dates Late"), "fieldname": "dates", "fieldtype": "Small Text", "width": 220},
	]

	# Stacked bar chart: x = employee, stacks = Grade 1, Grade 2, Grade 3
	chart = {
		"data": {
			"labels": [d.employee_name or d.employee for d in data],
			"datasets": [
				{"name": _("Grade 1"), "values": [d.g1 for d in data]},
				{"name": _("Grade 2"), "values": [d.g2 for d in data]},
				{"name": _("Grade 3"), "values": [d.g3 for d in data]},
			],
		},
		"type": "bar",
		"barOptions": {
			"stacked": 1,
		},
		"colors": ["#f39c12", "#e67e22", "#e74c3c"],
	}

	return columns, data, None, chart
