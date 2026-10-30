import frappe
from frappe import _
from frappe.utils import get_first_day, today, cint


def execute(filters=None):
	filters = frappe._dict(filters or {})
	min_count = cint(filters.min_count) or cint(
		frappe.db.get_single_value("Attendance Policy Settings", "habitual_threshold")
	) or 3
	from attendance_policy.tasks import get_exempt_employees, settings
	s = settings()
	exempt_emps = list(get_exempt_employees(s))

	conditions = ["attendance_date between %s and %s"]
	params = [filters.from_date or get_first_day(today()), filters.to_date or today()]

	if exempt_emps:
		conditions.append("employee not in ({})".format(", ".join(["%s"] * len(exempt_emps))))
		params.extend(exempt_emps)

	params.append(min_count)

	data = frappe.db.sql(
		f"""
		select employee, employee_name, department,
			sum(grade = 'Grade 1') as g1, sum(grade = 'Grade 2') as g2, sum(grade = 'Grade 3') as g3,
			count(*) as total, sum(deduction_days) as days
		from `tabLate Arrival Log`
		where {" and ".join(conditions)}
		group by employee, employee_name, department
		having count(*) >= %s
		order by total desc
		""",
		params,
		as_dict=True,
	)
	columns = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Grade 1"), "fieldname": "g1", "fieldtype": "Int", "width": 80},
		{"label": _("Grade 2"), "fieldname": "g2", "fieldtype": "Int", "width": 80},
		{"label": _("Grade 3"), "fieldname": "g3", "fieldtype": "Int", "width": 80},
		{"label": _("Total Late"), "fieldname": "total", "fieldtype": "Int", "width": 90},
		{"label": _("Deduction Days"), "fieldname": "days", "fieldtype": "Float", "precision": 2, "width": 110},
	]
	chart = {
		"data": {"labels": [d.employee_name for d in data], "datasets": [{"name": _("Late count"), "values": [d.total for d in data]}]},
		"type": "bar",
	}
	return columns, data, None, chart
