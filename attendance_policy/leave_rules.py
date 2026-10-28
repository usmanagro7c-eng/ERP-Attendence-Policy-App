import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months, today

from attendance_policy.tasks import is_holiday


def validate_leave_application(doc, method=None):
	s = frappe.get_single("Attendance Policy Settings")
	if s.casual_leave_type and doc.leave_type == s.casual_leave_type:
		_casual(doc, s)
	elif s.annual_leave_type and doc.leave_type == s.annual_leave_type:
		_annual(doc, s)


def _casual(doc, s):
	max_days = s.max_consecutive_casual or 3
	if (doc.total_leave_days or 0) > max_days:
		frappe.throw(_("Casual/Sick leave cannot exceed {0} consecutive days.").format(max_days))
	# Sundays/holidays joined to casual leave count as leave unless justified
	before, after = add_days(getdate(doc.from_date), -1), add_days(getdate(doc.to_date), 1)
	if (is_holiday(doc.employee, before) or is_holiday(doc.employee, after)) and not (doc.description or "").strip():
		frappe.throw(_("This leave is adjacent to a Sunday/holiday, which will count as leave. Please enter the Reason to justify, otherwise the holiday is counted as leave."))


def _annual(doc, s):
	doj = frappe.db.get_value("Employee", doc.employee, "date_of_joining")
	if doj and add_months(getdate(doj), 12) > getdate(doc.from_date):
		frappe.throw(_("Annual leave is available only after 12 months of continuous service."))
	if getdate(doc.from_date) <= getdate(today()) and "HR Manager" not in frappe.get_roles():
		frappe.throw(_("Annual leave needs prior approval. Apply before the leave starts; it cannot be used as casual leave."))
	year = getdate(doc.from_date).year
	parts = frappe.db.count("Leave Application", {
		"employee": doc.employee, "leave_type": doc.leave_type, "docstatus": ["<", 2],
		"status": ["!=", "Rejected"], "name": ["!=", doc.name or ""],
		"from_date": ["between", [f"{year}-01-01", f"{year}-12-31"]],
	})
	if parts >= 2:
		frappe.throw(_("Annual leave can be availed in at most two parts in a year."))
