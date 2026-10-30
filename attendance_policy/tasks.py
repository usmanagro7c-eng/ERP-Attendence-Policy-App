import frappe
from datetime import datetime, time as dtime
from frappe import _
from frappe.utils import (
	cint,
	escape_html,
	flt,
	format_time,
	get_first_day,
	get_last_day,
	get_time,
	getdate,
	today,
)


def settings():
	return frappe.get_single("Attendance Policy Settings")


def is_holiday(employee, date):
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

	hl = get_holiday_list_for_employee(employee, raise_exception=False)
	return bool(hl and frappe.db.exists("Holiday", {"parent": hl, "holiday_date": getdate(date)}))


def on_leave(employee, date, check_half_day=False):
	"""Returns True if employee is on approved leave.
	If check_half_day=True, returns tuple: (is_on_leave, is_half_day)
	"""
	filters = {
		"employee": employee,
		"docstatus": 1,
		"status": "Approved",
		"from_date": ["<=", date],
		"to_date": [">=", date],
	}
	leaves = frappe.get_all("Leave Application", filters=filters, fields=["name", "half_day", "half_day_date"])
	if not leaves:
		return (False, False) if check_half_day else False
	
	is_half = any(l.half_day and (not l.half_day_date or getdate(l.half_day_date) == getdate(date)) for l in leaves)
	if check_half_day:
		return True, is_half
	return True


def get_grade(arrival, s):
	"""arrival: datetime.time -> (grade, deduction_days) or (None, 0)"""
	if arrival <= get_time(s.arrival_cutoff or "09:00:00"):
		return None, 0
	if arrival >= get_time(s.second_half_cutoff or "13:30:00"):
		return "Grade 3", flt(s.full_day_deduction if s.full_day_deduction is not None else 1)
	if arrival <= get_time(s.grade1_end or "10:00:00"):
		return "Grade 1", flt(s.grade1_deduction)
	if arrival <= get_time(s.grade2_end or "11:00:00"):
		return "Grade 2", flt(s.grade2_deduction)
	return "Grade 3", flt(s.grade3_deduction)


# ---------------- Daily Job ----------------
def daily_job(date=None):
	s = settings()
	date = getdate(date or today())
	start_dt = datetime.combine(date, dtime.min)
	end_dt = datetime.combine(date, dtime.max)

	# Fetch valid checkins (optionally include or exclude skip_auto_attendance=1)
	checkin_filters = {
		"time": ["between", [start_dt, end_dt]],
	}
	if not getattr(s, "include_skip_auto_attendance_checkins", 1):
		checkin_filters["skip_auto_attendance"] = 0

	logs = frappe.get_all(
		"Employee Checkin",
		filters=checkin_filters,
		fields=["name", "employee", "employee_name", "time", "log_type"],
		order_by="time asc",
	)

	by = {}
	for l in logs:
		by.setdefault(l.employee, []).append(l)

	rows = []
	for emp, ls in by.items():
		try:
			process_daily_employee(emp, ls, date, s, rows)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Daily attendance processing failed for {emp}")

	absent = []
	if not is_holiday_company_wide(date):
		emp_filters = {"status": "Active"}
		if getattr(s, "company", None):
			emp_filters["company"] = s.company
		active_emps = frappe.get_all(
			"Employee",
			filters=emp_filters,
			fields=["name", "employee_name", "date_of_joining", "relieving_date"],
		)
		for e in active_emps:
			# Check joining and relieving dates
			if e.date_of_joining and getdate(e.date_of_joining) > date:
				continue
			if e.relieving_date and getdate(e.relieving_date) < date:
				continue
			if e.name not in by and not is_holiday(e.name, date) and not on_leave(e.name, date):
				absent.append(e.employee_name or e.name)

	# Habitual late-comers
	hab = habitual_this_month(s, date)

	# Send email
	send_daily_email(s, date, rows, absent, hab)

	# Send in-app notification to HR Managers
	if s.enable_hr_notification:
		send_hr_notification(s, date, rows, absent, hab)


def process_daily_employee(emp, ls, date, s, rows):
	emp_details = frappe.db.get_value(
		"Employee", emp, ["status", "company", "date_of_joining", "relieving_date", "employee_name", "department"], as_dict=True
	)
	if not emp_details or emp_details.status != "Active":
		return
	if getattr(s, "company", None) and emp_details.company and emp_details.company != s.company:
		return
	if emp_details.date_of_joining and getdate(emp_details.date_of_joining) > date:
		return
	if emp_details.relieving_date and getdate(emp_details.relieving_date) < date:
		return

	# Handle arrival & exit via IN/OUT logic
	in_logs = [l for l in ls if l.log_type == "IN"]
	out_logs = [l for l in ls if l.log_type == "OUT"]

	first_log = in_logs[0] if in_logs else ls[0]
	last_log = out_logs[-1] if out_logs else (ls[-1] if len(ls) > 1 else None)

	# Ensure exit is strictly after arrival if it exists
	if last_log and last_log.time <= first_log.time and len(ls) > 1:
		last_candidates = [l for l in ls if l.time > first_log.time]
		last_log = last_candidates[-1] if last_candidates else None

	first = first_log.time
	last = last_log.time if last_log else None
	grade = None
	days = 0

	has_leave, is_half_day = on_leave(emp, date, check_half_day=True)
	skip_due_to_half_day = is_half_day and s.skip_morning_late_if_half_day_leave

	if not is_holiday(emp, date) and not (has_leave and not skip_due_to_half_day):
		if not skip_due_to_half_day:
			grade, days = get_grade(first.time(), s)

		existing_log_name = frappe.db.get_value("Late Arrival Log", {"employee": emp, "attendance_date": date})
		if grade:
			if not existing_log_name:
				frappe.get_doc({
					"doctype": "Late Arrival Log",
					"employee": emp,
					"employee_name": emp_details.employee_name or ls[0].employee_name,
					"department": emp_details.department,
					"attendance_date": date,
					"arrival_time": first.time(),
					"exit_time": last.time() if last else None,
					"grade": grade,
					"deduction_days": days,
					"status": "Pending",
				}).insert(ignore_permissions=True)
			else:
				# Update exit time and recalculate if arrival changed on pending log
				existing_log = frappe.get_doc("Late Arrival Log", existing_log_name)
				if existing_log.status == "Pending":
					updated = False
					if last and existing_log.exit_time != last.time():
						existing_log.exit_time = last.time()
						updated = True
					if existing_log.arrival_time != first.time():
						existing_log.arrival_time = first.time()
						existing_log.grade = grade
						existing_log.deduction_days = days
						updated = True
					if updated:
						existing_log.save(ignore_permissions=True)
		elif existing_log_name:
			# Arrival changed to on-time while pending
			existing_log = frappe.get_doc("Late Arrival Log", existing_log_name)
			if existing_log.status == "Pending":
				if last and existing_log.exit_time != last.time():
					existing_log.exit_time = last.time()
					existing_log.save(ignore_permissions=True)

	rows.append((emp_details.employee_name or ls[0].employee_name, first, last, grade))


def is_holiday_company_wide(date):
	return getdate(date).weekday() == 6  # Sunday


def habitual_this_month(s, date):
	threshold = cint(s.habitual_threshold) or 3
	return frappe.db.sql(
		"""
		select employee_name, count(*) c, sum(grade='Grade 1') g1, sum(grade='Grade 2') g2, sum(grade='Grade 3') g3
		from `tabLate Arrival Log`
		where attendance_date between %s and %s
		group by employee, employee_name having count(*) >= %s order by c desc
		""",
		(get_first_day(date), date, threshold),
		as_dict=True,
	)


@frappe.whitelist()
def get_habitual_count():
	s = settings()
	hab = habitual_this_month(s, today())
	return len(hab) if hab else 0


def send_daily_email(s, date, rows, absent, hab=None):
	recipients = [r.strip() for r in (s.report_recipients or "").replace("\n", ",").split(",") if r.strip()]
	if not recipients:
		return
	td = "style='border:1px solid #ccc;padding:4px 8px'"
	body = [
		f"<h3>Attendance Report - {date.strftime('%A, %d %b %Y')}</h3>",
		"<table style='border-collapse:collapse'><tr>"
		+ "".join(f"<th {td}>{h}</th>" for h in ("Employee", "Check-in", "Check-out", "Late"))
		+ "</tr>",
	]
	for name, first, last, grade in sorted(rows, key=lambda r: r[1]):
		body.append(
			f"<tr><td {td}>{escape_html(name or '')}</td><td {td}>{format_time(first.time())}</td>"
			f"<td {td}>{format_time(last.time()) if last else '-'}</td><td {td}>{grade or ''}</td></tr>"
		)
	body.append("</table>")
	if absent:
		body.append(f"<p><b>No check-in ({len(absent)}):</b> " + escape_html(", ".join(absent)) + "</p>")
	if hab:
		body.append(
			"<h4>Habitual late-comers this month</h4><ul>"
			+ "".join(
				f"<li>{escape_html(h.employee_name)}: {h.c} times (G1 {int(h.g1)}, G2 {int(h.g2)}, G3 {int(h.g3)})</li>"
				for h in hab
			)
			+ "</ul>"
		)
	frappe.sendmail(recipients=recipients, subject=f"Daily Attendance Report - {date}", message="".join(body))


def send_hr_notification(s, date, rows, absent, hab=None):
	total_checked = len(rows)
	g1 = sum(1 for r in rows if r[3] == "Grade 1")
	g2 = sum(1 for r in rows if r[3] == "Grade 2")
	g3 = sum(1 for r in rows if r[3] == "Grade 3")
	total_late = g1 + g2 + g3
	absent_count = len(absent)
	hab_count = len(hab) if hab else 0

	subject = f"Daily Attendance Summary - {date}"
	content = (
		f"Daily attendance for {date.strftime('%d %b %Y')}: "
		f"{total_checked} checked in, {total_late} late (G1: {g1}, G2: {g2}, G3: {g3}), "
		f"{absent_count} absent, {hab_count} habitual late-comer(s)."
	)

	# Get all users with HR Manager role
	hr_managers = frappe.get_all(
		"Has Role",
		filters={"role": "HR Manager", "parenttype": "User"},
		pluck="parent",
	)
	hr_managers = list(set(hr_managers))

	for user in hr_managers:
		if not frappe.db.get_value("User", user, "enabled"):
			continue
		# Deduplication check: do not recreate if already exists for this date and user
		exists = frappe.db.exists(
			"Notification Log",
			{
				"for_user": user,
				"subject": subject,
				"document_type": "Report",
				"document_name": "Daily Attendance Summary",
			},
		)
		if not exists:
			n = frappe.new_doc("Notification Log")
			n.for_user = user
			n.type = "Alert"
			n.document_type = "Report"
			n.document_name = "Daily Attendance Summary"
			n.subject = subject
			n.email_content = content
			n.insert(ignore_permissions=True)


# ---------------- Month End ----------------
def calculate_employee_deduction(emp, ls, period_end, s):
	"""Reusable calculation of deduction split without mutating DB."""
	total = flt(sum(flt(l.deduction_days) for l in ls), 4)
	from_leave = 0.0

	if s.deduct_from_leave_first and s.casual_leave_type:
		from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

		bal = flt(get_leave_balance_on(emp, s.casual_leave_type, period_end))
		from_leave = min(max(bal, 0.0), total)

	from_salary = flt(total - from_leave, 4)
	base = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": emp, "docstatus": 1, "from_date": ["<=", period_end]},
		"base",
		order_by="from_date desc",
	)
	amount = 0.0
	if from_salary > 0 and base:
		amount = round(flt(base) / (s.salary_days_divisor or 30) * from_salary, 2)

	# Format list of months/dates covered
	dates = sorted(list(set(str(l.get("attendance_date") or "") for l in ls if l.get("attendance_date"))))
	periods_str = ", ".join(dates) if dates else str(period_end)

	return {
		"total": total,
		"from_leave": from_leave,
		"from_salary": from_salary,
		"base": flt(base or 0.0),
		"amount": amount,
		"periods_str": periods_str,
	}


def month_end_job(date=None):
	d = getdate(date or today())
	if d != get_last_day(d):
		return
	s = settings()

	# Pick ALL pending logs with attendance_date <= d (Fix 7: includes stale pending logs)
	logs = frappe.get_all(
		"Late Arrival Log",
		filters={"status": "Pending", "attendance_date": ["<=", d]},
		fields=["name", "employee", "employee_name", "attendance_date", "deduction_days"],
		order_by="attendance_date asc",
	)
	by = {}
	for l in logs:
		by.setdefault(l.employee, []).append(l)

	for emp, ls in by.items():
		try:
			process_employee(emp, ls, d, s)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Late deduction failed: {emp}")


def process_employee(emp, ls, period_end, s):
	calc = calculate_employee_deduction(emp, ls, period_end, s)
	total = calc["total"]
	from_leave = calc["from_leave"]
	from_salary = calc["from_salary"]
	company = frappe.db.get_value("Employee", emp, "company")

	entry = frappe.get_doc({
		"doctype": "Late Deduction Entry",
		"employee": emp,
		"period_end": period_end,
		"late_days": total,
		"from_leave": from_leave,
		"from_salary": from_salary,
		"included_periods": calc["periods_str"],
	}).insert(ignore_permissions=True)

	if from_leave > 0:
		lle = frappe.get_doc({
			"doctype": "Leave Ledger Entry",
			"employee": emp,
			"company": company,
			"leave_type": s.casual_leave_type,
			"transaction_type": "Late Deduction Entry",
			"transaction_name": entry.name,
			"leaves": -from_leave,
			"from_date": period_end,
			"to_date": period_end,
			"is_carry_forward": 0,
			"is_expired": 0,
		})
		lle.insert(ignore_permissions=True)
		lle.submit()
		entry.leave_ledger_entry = lle.name

	if from_salary > 0:
		if not calc["base"]:
			frappe.throw(f"No Salary Structure Assignment for {emp}")
		amount = calc["amount"]
		# Idempotent cleanup of any pre-existing Additional Salary for this period
		existing_ads = frappe.get_all(
			"Additional Salary",
			filters={"employee": emp, "salary_component": s.salary_component, "payroll_date": period_end},
			pluck="name",
		)
		for ads_name in existing_ads:
			try:
				ads_doc = frappe.get_doc("Additional Salary", ads_name)
				if ads_doc.docstatus == 1:
					ads_doc.cancel()
				ads_doc.delete()
			except Exception:
				pass

		add = frappe.get_doc({
			"doctype": "Additional Salary",
			"employee": emp,
			"company": company,
			"salary_component": s.salary_component,
			"amount": amount,
			"payroll_date": period_end,
			"overwrite_salary_structure_amount": 1,
		})
		add.insert(ignore_permissions=True)
		add.submit()
		entry.additional_salary, entry.salary_amount = add.name, amount

		if s.create_journal_entry and s.je_debit_account and s.je_credit_account:
			je = frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"company": company,
				"posting_date": period_end,
				"user_remark": f"Late arrival deduction {emp} {period_end}",
				"accounts": [
					{"account": s.je_debit_account, "debit_in_account_currency": amount},
					{"account": s.je_credit_account, "credit_in_account_currency": amount},
				],
			})
			je.insert(ignore_permissions=True)
			entry.journal_entry = je.name

	entry.save(ignore_permissions=True)
	for l in ls:
		frappe.db.set_value("Late Arrival Log", l.name, {"status": "Processed", "deduction_entry": entry.name})
	
	return entry.name
