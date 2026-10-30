import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	cint,
	flt,
	get_first_day,
	get_last_day,
	get_time,
	getdate,
	validate_email_address,
)


class AttendancePolicySettings(Document):
	def validate(self):
		self.validate_fractions()
		self.validate_timings()
		self.validate_numeric_fields()
		self.validate_leave_types()
		self.validate_salary_component()
		self.validate_journal_entry_settings()
		self.validate_recipients()
		self.validate_exempt_employees()

	def validate_fractions(self):
		for fld in ["grade1_deduction", "grade2_deduction", "grade3_deduction"]:
			val = flt(self.get(fld))
			if val < 0 or val > 1:
				frappe.throw(_("{0} deduction fraction must be between 0.0 and 1.0.").format(fld.replace("_", " ").title()))
		
		full_day = flt(self.full_day_deduction)
		if full_day < 0 or full_day > 1:
			frappe.throw(_("Full-day deduction fraction must be between 0.0 and 1.0."))

	def validate_timings(self):
		arrival = get_time(self.arrival_cutoff or "09:00:00")
		g1 = get_time(self.grade1_end or "10:00:00")
		g2 = get_time(self.grade2_end or "11:00:00")
		second_half = get_time(self.second_half_cutoff or "13:30:00")

		if not (arrival < g1 < g2 < second_half):
			frappe.throw(_("Timings must be in strict ascending order: Arrival Cutoff < Grade 1 End < Grade 2 End < Second Half Cutoff."))

	def validate_numeric_fields(self):
		if cint(self.salary_days_divisor) <= 0:
			frappe.throw(_("Days in month for per-day salary divisor must be greater than 0."))
		if cint(self.habitual_threshold) < 1:
			frappe.throw(_("Habitual late-comer threshold must be at least 1."))
		if cint(self.max_consecutive_casual) < 1:
			frappe.throw(_("Max consecutive casual days must be at least 1."))
		if cint(self.max_encashable_days) < 0:
			frappe.throw(_("Max encashable casual days cannot be negative."))

	def validate_leave_types(self):
		if not self.casual_leave_type or not self.annual_leave_type:
			frappe.throw(_("Both Casual/Sick Leave Type and Annual Leave Type must be configured."))
		if self.casual_leave_type == self.annual_leave_type:
			frappe.throw(_("Casual Leave Type and Annual Leave Type must be different."))

	def validate_salary_component(self):
		if self.salary_component:
			ctype = frappe.db.get_value("Salary Component", self.salary_component, "type")
			if ctype != "Deduction":
				frappe.throw(_("Salary Component '{0}' must be of type 'Deduction'.").format(self.salary_component))

	def validate_journal_entry_settings(self):
		if self.create_journal_entry:
			if not self.je_debit_account or not self.je_credit_account:
				frappe.throw(_("Both Debit Account and Credit Account are mandatory when Create Journal Entry is enabled."))
			
			if self.company:
				for acc in [self.je_debit_account, self.je_credit_account]:
					acc_comp = frappe.db.get_value("Account", acc, "company")
					if acc_comp and acc_comp != self.company:
						frappe.throw(_("Account '{0}' does not belong to Company '{1}'.").format(acc, self.company))
			
			for acc in [self.je_debit_account, self.je_credit_account]:
				atype = frappe.db.get_value("Account", acc, "account_type")
				if atype in ("Receivable", "Payable"):
					frappe.throw(_("Account '{0}' cannot be of type Receivable or Payable. Please select general asset/expense accounts.").format(acc))

	def validate_recipients(self):
		if self.report_recipients:
			emails = [e.strip() for e in self.report_recipients.replace("\n", ",").split(",") if e.strip()]
			for email in emails:
				validate_email_address(email, throw=True)

	def validate_exempt_employees(self):
		seen = set()
		for row in getattr(self, "exempt_employees", []) or []:
			if row.employee:
				if row.employee in seen:
					frappe.throw(_("Employee {0} is added more than once in Exempt Employees table.").format(row.employee))
				seen.add(row.employee)


@frappe.whitelist()
def process_month_end(period_end, dry_run=False):
	"""Manually trigger month-end processing for a given date.
	period_end: YYYY-MM-DD (must be last day of month)
	dry_run: if True, returns preview without committing changes
	"""
	frappe.only_for(["HR Manager", "System Manager"])
	from attendance_policy.tasks import calculate_employee_deduction, process_employee, settings

	period_end = getdate(period_end)
	if period_end != get_last_day(period_end):
		frappe.throw(_("Period end must be the last day of the month ({0})").format(get_last_day(period_end)))

	dry_run = cint(dry_run)
	s = settings()

	# Pick ALL pending logs with attendance_date <= period_end (Fix 7: includes stale pending logs)
	logs = frappe.get_all(
		"Late Arrival Log",
		filters={
			"status": "Pending",
			"attendance_date": ["<=", period_end],
		},
		fields=["name", "employee", "employee_name", "attendance_date", "deduction_days"],
		order_by="attendance_date asc",
	)

	# Group by employee
	by_emp = {}
	for l in logs:
		by_emp.setdefault(l.employee, []).append(l)

	results = []
	for emp, ls in by_emp.items():
		emp_name = ls[0].employee_name or frappe.db.get_value("Employee", emp, "employee_name") or emp
		calc = calculate_employee_deduction(emp, ls, period_end, s)

		if dry_run:
			results.append({
				"employee": emp,
				"employee_name": emp_name,
				"late_days": calc["total"],
				"from_leave": calc["from_leave"],
				"from_salary": calc["from_salary"],
				"salary_amount": calc["amount"],
				"logs": len(ls),
				"dates_covered": calc["periods_str"],
			})
		else:
			try:
				entry_name = process_employee(emp, ls, period_end, s)
				frappe.db.commit()
				results.append({
					"employee": emp,
					"employee_name": emp_name,
					"status": "Success",
					"late_days": calc["total"],
					"from_leave": calc["from_leave"],
					"from_salary": calc["from_salary"],
					"salary_amount": calc["amount"],
					"entry": entry_name,
				})
			except Exception as e:
				frappe.db.rollback()
				frappe.log_error(title=f"Month-end processing failed for {emp}")
				results.append({
					"employee": emp,
					"employee_name": emp_name,
					"status": "Failed",
					"error": str(e),
				})

	return {
		"period_end": str(period_end),
		"dry_run": bool(dry_run),
		"employees_processed": len(results),
		"details": results,
	}
