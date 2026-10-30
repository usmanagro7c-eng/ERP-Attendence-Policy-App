import frappe
from frappe import _
from frappe.utils import (
	add_days,
	add_months,
	flt,
	getdate,
	today,
)

from attendance_policy.tasks import get_exempt_employees, is_holiday


def validate_leave_application(doc, method=None):
	s = frappe.get_single("Attendance Policy Settings")
	if doc.employee in get_exempt_employees(s):
		return
	if s.casual_leave_type and doc.leave_type == s.casual_leave_type:
		_casual(doc, s)
	elif s.annual_leave_type and doc.leave_type == s.annual_leave_type:
		_annual(doc, s)


def get_adjacent_holiday_chain(employee, from_date, to_date):
	"""Returns list of holiday dates immediately adjacent to from_date (before) and to_date (after).
	Handles chains (e.g. Saturday leave followed by Sunday + Monday holiday).
	"""
	from_d = getdate(from_date)
	to_d = getdate(to_date)

	# Walk backwards before from_d
	before_holidays = []
	cur = add_days(from_d, -1)
	while is_holiday(employee, cur):
		before_holidays.append(cur)
		cur = add_days(cur, -1)
	before_holidays.reverse()

	# Walk forwards after to_d
	after_holidays = []
	cur = add_days(to_d, 1)
	while is_holiday(employee, cur):
		after_holidays.append(cur)
		cur = add_days(cur, 1)

	return before_holidays, after_holidays


def _casual(doc, s):
	max_days = s.max_consecutive_casual or 3
	has_reason = bool((doc.description or "").strip())
	before_hols, after_hols = get_adjacent_holiday_chain(doc.employee, doc.from_date, doc.to_date)
	total_adj_hols = len(before_hols) + len(after_hols)

	# Check consecutive days cap
	applied_days = flt(doc.total_leave_days or 0)
	cap_check_days = applied_days
	if s.count_adjacent_holidays and not has_reason and s.adjacent_holidays_in_3day_cap:
		cap_check_days += total_adj_hols

	if cap_check_days > max_days:
		frappe.throw(_("Casual/Sick leave cannot exceed {0} consecutive days.").format(max_days))

	# Adjacent holiday counting
	if s.count_adjacent_holidays and total_adj_hols > 0:
		if not has_reason:
			all_dates = [str(d) for d in (before_hols + after_hols)]
			frappe.msgprint(
				_(
					"This leave is adjacent to {0} holiday/Sunday day(s) ({1}). "
					"Because no justification was provided in the Reason field, these day(s) "
					"will be counted as leave and deducted from your casual balance upon approval."
				).format(total_adj_hols, ", ".join(all_dates)),
				title=_("Adjacent Holiday Policy"),
				indicator="orange",
			)


def on_leave_application_submit(doc, method=None):
	"""On submission, if Reason is empty and adjacent holidays exist, create extra Leave Ledger Entry."""
	s = frappe.get_single("Attendance Policy Settings")
	if doc.employee in get_exempt_employees(s):
		return
	if not (s.casual_leave_type and doc.leave_type == s.casual_leave_type and s.count_adjacent_holidays):
		return
	if (doc.description or "").strip():
		return

	from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

	before_hols, after_hols = get_adjacent_holiday_chain(doc.employee, doc.from_date, doc.to_date)
	total_extra = len(before_hols) + len(after_hols)
	if total_extra <= 0:
		return

	holiday_list = get_holiday_list_for_employee(doc.employee, raise_exception=False) or ""

	# Build separate contiguous entries for before and after runs
	for hols in [before_hols, after_hols]:
		if not hols:
			continue
		start_date = hols[0]
		end_date = hols[-1]
		count = len(hols)
		args = frappe._dict(
			leaves=-count,
			from_date=start_date,
			to_date=end_date,
			holiday_list=holiday_list,
			is_lwp=0,
		)
		create_leave_ledger_entry(doc, args, submit=True)


def on_leave_application_cancel(doc, method=None):
	"""Clean up any extra Leave Ledger Entries on cancel (HRMS built-in delete_ledger_entry also handles this)."""
	from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
	try:
		create_leave_ledger_entry(doc, {}, submit=False)
	except Exception:
		pass


def _annual(doc, s):
	doj = frappe.db.get_value("Employee", doc.employee, "date_of_joining")
	if doj and add_months(getdate(doj), 12) > getdate(doc.from_date):
		frappe.throw(_("Annual leave is available only after 12 months of continuous service."))
	if getdate(doc.from_date) <= getdate(today()) and "HR Manager" not in frappe.get_roles():
		frappe.throw(_("Annual leave needs prior approval. Apply before the leave starts; it cannot be used as casual leave."))
	year = getdate(doc.from_date).year
	parts = frappe.db.count("Leave Application", {
		"employee": doc.employee,
		"leave_type": doc.leave_type,
		"docstatus": ["<", 2],
		"status": ["!=", "Rejected"],
		"name": ["!=", doc.name or ""],
		"from_date": ["between", [f"{year}-01-01", f"{year}-12-31"]],
	})
	if parts >= 2:
		frappe.throw(_("Annual leave can be availed in at most two parts in a year."))


def validate_leave_encashment(doc, method=None):
	s = frappe.get_single("Attendance Policy Settings")
	if doc.employee in get_exempt_employees(s):
		return
	if not (s.casual_leave_type and doc.leave_type == s.casual_leave_type):
		return
	max_days = flt(s.max_encashable_days if s.max_encashable_days is not None else 10)
	enc_date = getdate(doc.encashment_date or today())
	year = enc_date.year

	existing = frappe.get_all(
		"Leave Encashment",
		filters={
			"employee": doc.employee,
			"leave_type": doc.leave_type,
			"docstatus": ["!=", 2],
			"name": ["!=", doc.name or ""],
			"encashment_date": ["between", [f"{year}-01-01", f"{year}-12-31"]],
		},
		fields=["encashment_days"],
	)
	total_encashed = sum(flt(e.encashment_days) for e in existing)
	if total_encashed + flt(doc.encashment_days) > max_days:
		frappe.throw(
			_(
				"Casual leave encashment cannot exceed {0} days in a calendar year. "
				"Already encashed: {1} days; requested: {2} days."
			).format(max_days, total_encashed, doc.encashment_days)
		)


def validate_salary_slip(doc, method=None):
	s = frappe.get_single("Attendance Policy Settings")
	if doc.employee in get_exempt_employees(s):
		return
	if not s.warn_salary_slip_pending_late:
		return
	if not (doc.employee and doc.start_date and doc.end_date):
		return
	pending = frappe.get_all(
		"Late Arrival Log",
		filters={
			"employee": doc.employee,
			"status": "Pending",
			"attendance_date": ["between", [doc.start_date, doc.end_date]],
		},
		fields=["name", "attendance_date", "grade"],
	)
	if pending:
		frappe.msgprint(
			_(
				"Warning: Employee {0} has {1} unprocessed pending Late Arrival Log(s) in this salary slip period ({2} to {3}). "
				"Ensure month-end attendance processing is completed before finalizing payroll."
			).format(doc.employee, len(pending), doc.start_date, doc.end_date),
			indicator="orange",
			title=_("Unprocessed Late Arrivals"),
		)
