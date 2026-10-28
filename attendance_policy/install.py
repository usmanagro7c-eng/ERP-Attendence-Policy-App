import frappe


def after_install():
	if not frappe.db.exists("Salary Component", "Late Arrival Deduction"):
		frappe.get_doc({"doctype": "Salary Component", "salary_component": "Late Arrival Deduction",
			"salary_component_abbr": "LAD", "type": "Deduction", "depends_on_payment_days": 0}).insert(ignore_permissions=True)
	make_dashboard()


def make_dashboard():
	common = {"doctype": "Dashboard Chart", "document_type": "Late Arrival Log", "is_public": 1,
		"filters_json": "[]", "module": "Attendance Policy"}
	charts = [
		("Late Arrivals by Grade", {"chart_type": "Group By", "group_by_type": "Count", "group_by_based_on": "grade", "type": "Bar"}),
		("Late Arrivals by Employee", {"chart_type": "Group By", "group_by_type": "Count", "group_by_based_on": "employee_name", "type": "Bar", "number_of_groups": 10}),
		("Late Arrivals Daily Trend", {"chart_type": "Count", "based_on": "attendance_date", "timeseries": 1,
			"time_interval": "Daily", "timespan": "Last Month", "type": "Line"}),
	]
	names = []
	for name, extra in charts:
		try:
			if not frappe.db.exists("Dashboard Chart", name):
				frappe.get_doc({**common, "chart_name": name, **extra}).insert(ignore_permissions=True)
			names.append(name)
		except Exception:
			frappe.log_error(title=f"Chart create failed: {name}")
	try:
		if names and not frappe.db.exists("Dashboard", "Late Arrivals"):
			frappe.get_doc({"doctype": "Dashboard", "dashboard_name": "Late Arrivals", "module": "Attendance Policy",
				"charts": [{"chart": n, "width": "Half"} for n in names]}).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="Dashboard create failed")
