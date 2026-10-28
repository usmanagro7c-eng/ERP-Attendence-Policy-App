import frappe
from datetime import datetime, time as dtime
from frappe.utils import (getdate, today, get_time, flt, get_first_day, get_last_day,
	format_time, escape_html)


def settings():
	return frappe.get_single("Attendance Policy Settings")


def is_holiday(employee, date):
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

	hl = get_holiday_list_for_employee(employee, raise_exception=False)
	return bool(hl and frappe.db.exists("Holiday", {"parent": hl, "holiday_date": getdate(date)}))


def on_leave(employee, date):
	return bool(frappe.db.exists("Leave Application", {
		"employee": employee, "docstatus": 1, "status": "Approved",
		"from_date": ["<=", date], "to_date": [">=", date]}))


def get_grade(arrival, s):
	"""arrival: datetime.time -> (grade, deduction_days) or (None, 0)"""
	if arrival <= get_time(s.arrival_cutoff or "09:00:00"):
		return None, 0
	if arrival >= get_time(s.second_half_cutoff or "13:30:00"):
		return "Grade 3", flt(s.full_day_deduction or 1)
	if arrival <= get_time(s.grade1_end or "10:00:00"):
		return "Grade 1", flt(s.grade1_deduction)
	if arrival <= get_time(s.grade2_end or "11:00:00"):
		return "Grade 2", flt(s.grade2_deduction)
	return "Grade 3", flt(s.grade3_deduction)


# ---------------- Daily ----------------
def daily_job(date=None):
	s = settings()
	date = getdate(date or today())
	logs = frappe.get_all("Employee Checkin", filters={"time": ["between", [
		datetime.combine(date, dtime.min), datetime.combine(date, dtime.max)]]},
		fields=["employee", "employee_name", "time"], order_by="time asc")
	by = {}
	for l in logs:
		by.setdefault(l.employee, []).append(l)

	rows = []
	for emp, ls in by.items():
		if frappe.db.get_value("Employee", emp, "status") != "Active":
			continue
		first, last = ls[0].time, (ls[-1].time if len(ls) > 1 else None)
		grade = None
		if not is_holiday(emp, date) and not on_leave(emp, date):
			grade, days = get_grade(first.time(), s)
			if grade and not frappe.db.exists("Late Arrival Log", {"employee": emp, "attendance_date": date}):
				frappe.get_doc({
					"doctype": "Late Arrival Log", "employee": emp, "employee_name": ls[0].employee_name,
					"attendance_date": date, "arrival_time": first.time(),
					"exit_time": last.time() if last else None,
					"grade": grade, "deduction_days": days, "status": "Pending"}).insert(ignore_permissions=True)
		rows.append((ls[0].employee_name, first, last, grade))

	absent = []
	if not is_holiday_company_wide(date):
		for e in frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name"]):
			if e.name not in by and not is_holiday(e.name, date) and not on_leave(e.name, date):
				absent.append(e.employee_name)
	frappe.db.commit()
	send_daily_email(s, date, rows, absent)


def is_holiday_company_wide(date):
	return getdate(date).weekday() == 6  # Sunday


def habitual_this_month(s, date):
	return frappe.db.sql("""
		select employee_name, count(*) c, sum(grade='Grade 1') g1, sum(grade='Grade 2') g2, sum(grade='Grade 3') g3
		from `tabLate Arrival Log` where attendance_date between %s and %s
		group by employee, employee_name having count(*) >= %s order by c desc""",
		(get_first_day(date), date, s.habitual_threshold or 3), as_dict=True)


def send_daily_email(s, date, rows, absent):
	recipients = [r.strip() for r in (s.report_recipients or "").replace("\n", ",").split(",") if r.strip()]
	if not recipients:
		return
	td = "style='border:1px solid #ccc;padding:4px 8px'"
	body = [f"<h3>Attendance Report - {date.strftime('%A, %d %b %Y')}</h3>",
		"<table style='border-collapse:collapse'><tr>" + "".join(f"<th {td}>{h}</th>" for h in ("Employee", "Check-in", "Check-out", "Late")) + "</tr>"]
	for name, first, last, grade in sorted(rows, key=lambda r: r[1]):
		body.append(f"<tr><td {td}>{escape_html(name or '')}</td><td {td}>{format_time(first.time())}</td>"
			f"<td {td}>{format_time(last.time()) if last else '-'}</td><td {td}>{grade or ''}</td></tr>")
	body.append("</table>")
	if absent:
		body.append(f"<p><b>No check-in ({len(absent)}):</b> " + escape_html(", ".join(absent)) + "</p>")
	hab = habitual_this_month(s, date)
	if hab:
		body.append("<h4>Habitual late-comers this month</h4><ul>" + "".join(
			f"<li>{escape_html(h.employee_name)}: {h.c} times (G1 {int(h.g1)}, G2 {int(h.g2)}, G3 {int(h.g3)})</li>" for h in hab) + "</ul>")
	frappe.sendmail(recipients=recipients, subject=f"Daily Attendance Report - {date}", message="".join(body))


# ---------------- Month end ----------------
def month_end_job(date=None):
	d = getdate(date or today())
	if d != get_last_day(d):
		return
	s = settings()
	logs = frappe.get_all("Late Arrival Log", filters={"status": "Pending",
		"attendance_date": ["between", [get_first_day(d), d]]}, fields=["name", "employee", "deduction_days"])
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
	total = flt(sum(flt(l.deduction_days) for l in ls), 4)
	company = frappe.db.get_value("Employee", emp, "company")
	from_leave = 0
	if s.deduct_from_leave_first and s.casual_leave_type:
		from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
		bal = flt(get_leave_balance_on(emp, s.casual_leave_type, period_end))
		from_leave = min(max(bal, 0), total)
	from_salary = flt(total - from_leave, 4)

	entry = frappe.get_doc({"doctype": "Late Deduction Entry", "employee": emp, "period_end": period_end,
		"late_days": total, "from_leave": from_leave, "from_salary": from_salary}).insert(ignore_permissions=True)

	if from_leave > 0:
		lle = frappe.get_doc({"doctype": "Leave Ledger Entry", "employee": emp, "company": company,
			"leave_type": s.casual_leave_type, "transaction_type": "Late Deduction Entry",
			"transaction_name": entry.name, "leaves": -from_leave,
			"from_date": period_end, "to_date": period_end, "is_carry_forward": 0, "is_expired": 0})
		lle.insert(ignore_permissions=True)
		lle.submit()
		entry.leave_ledger_entry = lle.name

	if from_salary > 0:
		base = frappe.db.get_value("Salary Structure Assignment",
			{"employee": emp, "docstatus": 1, "from_date": ["<=", period_end]}, "base", order_by="from_date desc")
		if not base:
			frappe.throw(f"No Salary Structure Assignment for {emp}")
		amount = round(flt(base) / (s.salary_days_divisor or 30) * from_salary, 2)
		add = frappe.get_doc({"doctype": "Additional Salary", "employee": emp, "company": company,
			"salary_component": s.salary_component, "amount": amount, "payroll_date": period_end,
			"overwrite_salary_structure_amount": 1})
		add.insert(ignore_permissions=True)
		add.submit()
		entry.additional_salary, entry.salary_amount = add.name, amount
		if s.create_journal_entry and s.je_debit_account and s.je_credit_account:
			je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": company,
				"posting_date": period_end, "user_remark": f"Late arrival deduction {emp} {period_end}",
				"accounts": [{"account": s.je_debit_account, "debit_in_account_currency": amount},
					{"account": s.je_credit_account, "credit_in_account_currency": amount}]})
			je.insert(ignore_permissions=True)
			entry.journal_entry = je.name
	entry.save(ignore_permissions=True)
	for l in ls:
		frappe.db.set_value("Late Arrival Log", l.name, {"status": "Processed", "deduction_entry": entry.name})
