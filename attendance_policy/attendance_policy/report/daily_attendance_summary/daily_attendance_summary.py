import frappe
from frappe import _
from frappe.utils import getdate, today
from datetime import datetime, time as dtime


def execute(filters=None):
	filters = frappe._dict(filters or {})
	date = getdate(filters.date or today())
	
	# Get all checkins for the date
	checkins = frappe.get_all(
		"Employee Checkin",
		filters={
			"time": ["between", [
				datetime.combine(date, dtime.min),
				datetime.combine(date, dtime.max)
			]]
		},
		fields=["employee", "employee_name", "time"],
		order_by="time asc"
	)
	
	# Group by employee
	by_emp = {}
	for c in checkins:
		if c.employee not in by_emp:
			by_emp[c.employee] = {"name": c.employee_name, "checkins": []}
		by_emp[c.employee]["checkins"].append(c.time)
	
	# Get late arrival logs for the date
	late_logs = frappe.get_all(
		"Late Arrival Log",
		filters={"attendance_date": date},
		fields=["employee", "grade", "arrival_time", "exit_time"]
	)
	late_map = {l.employee: l for l in late_logs}
	
	data = []
	for emp, info in by_emp.items():
		checkins = info["checkins"]
		first = checkins[0] if checkins else None
		last = checkins[-1] if len(checkins) > 1 else None
		late_info = late_map.get(emp, {})
		
		data.append({
			"employee": emp,
			"employee_name": info["name"],
			"check_in": first.time() if first else None,
			"check_out": last.time() if last else None,
			"late_grade": late_info.get("grade", ""),
			"status": "Late" if late_info else "On Time"
		})
	
	# Sort by check-in time
	data.sort(key=lambda x: x["check_in"] or dtime.max)
	
	columns = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Check-in"), "fieldname": "check_in", "fieldtype": "Time", "width": 100},
		{"label": _("Check-out"), "fieldname": "check_out", "fieldtype": "Time", "width": 100},
		{"label": _("Late Grade"), "fieldname": "late_grade", "fieldtype": "Data", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
	]
	
	return columns, data
