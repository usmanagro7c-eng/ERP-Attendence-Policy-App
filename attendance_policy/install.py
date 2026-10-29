import frappe
from datetime import date, timedelta
from frappe import _
from frappe.utils import getdate, today


def after_install():
	if not frappe.db.exists("Salary Component", "Late Arrival Deduction"):
		frappe.get_doc({
			"doctype": "Salary Component",
			"salary_component": "Late Arrival Deduction",
			"salary_component_abbr": "LAD",
			"type": "Deduction",
			"depends_on_payment_days": 0,
		}).insert(ignore_permissions=True)
	make_dashboard()
	make_number_cards()


def make_number_cards():
	cards = [
		{
			"doctype": "Number Card",
			"name": "Late Today",
			"label": "Late Today",
			"type": "Document Type",
			"document_type": "Late Arrival Log",
			"function": "Count",
			"is_public": 1,
			"module": "Attendance Policy",
			"filters_json": '[["Late Arrival Log","attendance_date","=","Today",false]]',
		},
		{
			"doctype": "Number Card",
			"name": "Late This Month",
			"label": "Late This Month",
			"type": "Document Type",
			"document_type": "Late Arrival Log",
			"function": "Count",
			"is_public": 1,
			"module": "Attendance Policy",
			"filters_json": '[["Late Arrival Log","attendance_date","Timespan","this month",false]]',
		},
		{
			"doctype": "Number Card",
			"name": "Habitual Late-Comers This Month",
			"label": "Habitual Late-Comers This Month",
			"type": "Custom",
			"method": "attendance_policy.tasks.get_habitual_count",
			"is_public": 1,
			"module": "Attendance Policy",
		},
	]
	for c in cards:
		try:
			if not frappe.db.exists("Number Card", c["name"]):
				frappe.get_doc(c).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title=f"Number card create failed: {c['name']}")


def make_dashboard():
	common = {
		"doctype": "Dashboard Chart",
		"document_type": "Late Arrival Log",
		"is_public": 1,
		"filters_json": "[]",
		"module": "Attendance Policy",
	}
	charts = [
		("Late Arrivals by Grade", {
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "grade",
			"type": "Bar",
		}),
		("Late Arrivals by Employee", {
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "employee_name",
			"type": "Bar",
			"number_of_groups": 10,
		}),
		("Late Arrivals Daily Trend", {
			"chart_type": "Count",
			"based_on": "attendance_date",
			"timeseries": 1,
			"time_interval": "Daily",
			"timespan": "Last Month",
			"type": "Line",
		}),
	]
	names = []
	for name, extra in charts:
		try:
			if not frappe.db.exists("Dashboard Chart", name):
				frappe.get_doc({**common, "chart_name": name, **extra}).insert(ignore_permissions=True)
			names.append(name)
		except Exception:
			frappe.log_error(title=f"Chart create failed: {name}")

	# Also add "Late Comers by Grade" report chart if report exists
	if frappe.db.exists("Report", "Late Comers by Grade") and not frappe.db.exists("Dashboard Chart", "Late Comers by Grade"):
		try:
			rep_chart = frappe.get_doc({
				"doctype": "Dashboard Chart",
				"chart_name": "Late Comers by Grade",
				"chart_type": "Report",
				"report_name": "Late Comers by Grade",
				"use_report_chart": 1,
				"is_public": 1,
				"module": "Attendance Policy",
			}).insert(ignore_permissions=True)
			names.append(rep_chart.name)
		except Exception:
			frappe.log_error(title="Report chart create failed")

	try:
		if names:
			if not frappe.db.exists("Dashboard", "Late Arrivals"):
				frappe.get_doc({
					"doctype": "Dashboard",
					"dashboard_name": "Late Arrivals",
					"module": "Attendance Policy",
					"charts": [{"chart": n, "width": "Half"} for n in names],
				}).insert(ignore_permissions=True)
			else:
				# Ensure all charts are present in dashboard
				dash = frappe.get_doc("Dashboard", "Late Arrivals")
				existing = [c.chart for c in dash.charts]
				for n in names:
					if n not in existing:
						dash.append("charts", {"chart": n, "width": "Half"})
				dash.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="Dashboard create/update failed")


@frappe.whitelist()
def create_default_configuration():
	"""Provisions default Shift Types, Leave Types, and Holiday List idempotently."""
	frappe.only_for(["HR Manager", "System Manager"])
	messages = []
	year = getdate(today()).year

	# 1. Shift Types
	shifts = [
		{
			"doctype": "Shift Type",
			"name": "Regular Shift (Mon-Thu, Sat)",
			"start_time": "08:30:00",
			"end_time": "17:30:00",
		},
		{
			"doctype": "Shift Type",
			"name": "Friday Shift",
			"start_time": "08:30:00",
			"end_time": "16:30:00",
		},
	]
	for s in shifts:
		if not frappe.db.exists("Shift Type", s["name"]):
			frappe.get_doc(s).insert(ignore_permissions=True)
			messages.append(_("Created Shift Type: {0}").format(s["name"]))
		else:
			messages.append(_("Shift Type already exists: {0}").format(s["name"]))

	# 2. Leave Types
	leave_types = [
		{
			"doctype": "Leave Type",
			"leave_type_name": "Casual Leave",
			"max_continuous_days_allowed": 3,
			"max_leaves_allowed": 15,
			"allow_encashment": 1,
			"max_encashable_leaves": 10,
			"include_holiday": 0,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": "Annual Leave",
			"max_leaves_allowed": 15,
			"applicable_after": 365,
			"include_holiday": 1,
		},
	]
	for lt in leave_types:
		if not frappe.db.exists("Leave Type", lt["leave_type_name"]):
			frappe.get_doc(lt).insert(ignore_permissions=True)
			messages.append(_("Created Leave Type: {0}").format(lt["leave_type_name"]))
		else:
			messages.append(_("Leave Type already exists: {0}").format(lt["leave_type_name"]))

	# 3. Holiday List
	hl_name = f"Default Holiday List {year}"
	if not frappe.db.exists("Holiday List", hl_name):
		from_d = date(year, 1, 1)
		to_d = date(year, 12, 31)
		hl = frappe.get_doc({
			"doctype": "Holiday List",
			"holiday_list_name": hl_name,
			"from_date": from_d,
			"to_date": to_d,
			"weekly_off": "Sunday",
		})
		
		# Generate Sunday dates
		cur = from_d
		while cur <= to_d:
			if cur.weekday() == 6:  # Sunday
				hl.append("holidays", {
					"holiday_date": cur,
					"description": "Sunday",
					"weekly_off": 1,
				})
			cur += timedelta(days=1)
		
		hl.insert(ignore_permissions=True)
		messages.append(_("Created Holiday List: {0} ({1} Sundays)").format(hl_name, len(hl.holidays)))
	else:
		messages.append(_("Holiday List already exists: {0}").format(hl_name))

	# Assign Holiday List to default company if not already assigned
	default_company = frappe.db.get_single_value("Global Defaults", "default_company")
	if default_company and not frappe.db.exists(
		"Holiday List Assignment",
		{"applicable_for": "Company", "assigned_to": default_company, "docstatus": 1},
	):
		try:
			hla = frappe.get_doc({
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": default_company,
				"holiday_list": hl_name,
				"from_date": date(year, 1, 1),
			})
			hla.insert(ignore_permissions=True)
			hla.submit()
			messages.append(_("Assigned Holiday List {0} to Company {1}").format(hl_name, default_company))
		except Exception:
			pass

	# 4. Salary Component
	if not frappe.db.exists("Salary Component", "Late Arrival Deduction"):
		frappe.get_doc({
			"doctype": "Salary Component",
			"salary_component": "Late Arrival Deduction",
			"salary_component_abbr": "LAD",
			"type": "Deduction",
			"depends_on_payment_days": 0,
		}).insert(ignore_permissions=True)
		messages.append(_("Created Salary Component: Late Arrival Deduction"))
	else:
		messages.append(_("Salary Component already exists: Late Arrival Deduction"))

	make_dashboard()
	make_number_cards()
	frappe.db.commit()
	return messages
