import frappe
from datetime import date, datetime, time as dtime, timedelta
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, get_first_day, get_last_day, getdate, today

from attendance_policy.tasks import (
	calculate_employee_deduction,
	daily_job,
	get_grade,
	get_habitual_count,
	habitual_this_month,
	is_holiday,
	month_end_job,
	on_leave,
	settings,
)
from attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings import (
	process_month_end,
)
from attendance_policy.install import create_default_configuration, make_dashboard, make_number_cards
from attendance_policy.leave_rules import get_adjacent_holiday_chain


class TestAttendancePolicy(IntegrationTestCase):
	"""Comprehensive test suite for Attendance Policy application."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.setup_company_and_settings()

	@classmethod
	def setup_company_and_settings(cls):
		frappe.set_user("Administrator")
		# 1. Company
		cls.company_name = "Test Attendance Company"
		if not frappe.db.exists("Company", cls.company_name):
			comp = frappe.get_doc({
				"doctype": "Company",
				"company_name": cls.company_name,
				"abbr": "TAC",
				"default_currency": "PKR",
				"country": "Pakistan",
			}).insert(ignore_permissions=True)
			cls.company = comp.name
		else:
			cls.company = cls.company_name

		# 2. Fiscal Years (2024 to 2027)
		for y in [2024, 2025, 2026, 2027]:
			fy_name = f"{y}"
			if not frappe.db.exists("Fiscal Year", fy_name):
				frappe.get_doc({
					"doctype": "Fiscal Year",
					"year": fy_name,
					"year_start_date": f"{y}-01-01",
					"year_end_date": f"{y}-12-31",
					"companies": [{"company": cls.company}],
				}).insert(ignore_permissions=True)
			else:
				fy = frappe.get_doc("Fiscal Year", fy_name)
				if not any(c.company == cls.company for c in fy.companies):
					fy.append("companies", {"company": cls.company})
					fy.save(ignore_permissions=True)

		# 3. Provision default configuration
		create_default_configuration()
		make_dashboard()
		make_number_cards()

		cls.casual_lt = "Casual Leave"
		cls.annual_lt = "Annual Leave"
		cls.holiday_list = f"Default Holiday List 2026"

		# Ensure Holiday List Assignment exists for Company
		if not frappe.db.exists("Holiday List Assignment", {"applicable_for": "Company", "assigned_to": cls.company, "docstatus": 1}):
			hla = frappe.get_doc({
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": cls.company,
				"holiday_list": cls.holiday_list,
				"from_date": "2026-01-01",
			})
			hla.insert(ignore_permissions=True)
			hla.submit()

		# Ensure Basic Salary component exists
		if not frappe.db.exists("Salary Component", "Basic Salary"):
			frappe.get_doc({
				"doctype": "Salary Component",
				"salary_component": "Basic Salary",
				"salary_component_abbr": "BS",
				"type": "Earning",
			}).insert(ignore_permissions=True)

		# Ensure Leave Period exists
		existing_lp = frappe.db.get_value("Leave Period", {"company": cls.company, "is_active": 1}, "name")
		if existing_lp:
			cls.leave_period = existing_lp
		else:
			lp = frappe.get_doc({
				"doctype": "Leave Period",
				"from_date": "2026-01-01",
				"to_date": "2026-12-31",
				"company": cls.company,
				"is_active": 1,
			}).insert(ignore_permissions=True)
			cls.leave_period = lp.name

		# 4. Settings
		s = frappe.get_single("Attendance Policy Settings")
		s.company = cls.company
		s.arrival_cutoff = "09:00:00"
		s.grade1_end = "10:00:00"
		s.grade2_end = "11:00:00"
		s.second_half_cutoff = "13:30:00"
		s.grade1_deduction = 0.166667
		s.grade2_deduction = 0.333333
		s.grade3_deduction = 0.5
		s.full_day_deduction = 1.0
		s.habitual_threshold = 3
		s.report_recipients = "hr_test@example.com"
		s.casual_leave_type = cls.casual_lt
		s.annual_leave_type = cls.annual_lt
		s.max_consecutive_casual = 3
		s.count_adjacent_holidays = 1
		s.adjacent_holidays_in_3day_cap = 0
		s.max_encashable_days = 10
		s.deduct_from_leave_first = 1
		s.salary_component = "Late Arrival Deduction"
		s.salary_days_divisor = 30
		s.enable_hr_notification = 1
		s.skip_morning_late_if_half_day_leave = 1
		s.warn_salary_slip_pending_late = 1
		s.create_journal_entry = 0
		s.save(ignore_permissions=True)

		# 5. Accounts for JE test
		cls.setup_accounts()

	@classmethod
	def setup_accounts(cls):
		accs = frappe.get_all(
			"Account",
			filters={"company": cls.company, "is_group": 0, "account_type": ["not in", ["Receivable", "Payable"]]},
			pluck="name",
		)
		if len(accs) >= 2:
			cls.acc_expense = accs[0]
			cls.acc_cash = accs[1]
		else:
			cls.acc_expense = None
			cls.acc_cash = None

	def create_employee(self, first_name, joining_date="2025-01-01", relieving_date=None, status="Active"):
		emp_name = f"TAP_{first_name}"
		existing = frappe.db.get_value("Employee", {"first_name": emp_name}, "name")
		if existing:
			frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee=%s", existing)
			frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee=%s", existing)
			frappe.db.commit()
			return existing

		emp = frappe.get_doc({
			"doctype": "Employee",
			"first_name": emp_name,
			"gender": "Female",
			"date_of_birth": "1994-05-15",
			"date_of_joining": joining_date,
			"relieving_date": relieving_date,
			"status": status,
			"company": self.company,
			"holiday_list": self.holiday_list,
			"leave_approver": "Administrator",
		}).insert(ignore_permissions=True)
		return emp.name

	def assign_salary(self, employee, base=60000, from_date="2026-01-01"):
		existing = frappe.db.get_value("Salary Structure Assignment", {"employee": employee, "docstatus": 1})
		if existing:
			return existing

		if not frappe.db.exists("Salary Component", "Basic Salary"):
			frappe.get_doc({
				"doctype": "Salary Component",
				"salary_component": "Basic Salary",
				"salary_component_abbr": "BS",
				"type": "Earning",
			}).insert(ignore_permissions=True)

		ss_name = "Test_TAP_Salary_Structure"
		if not frappe.db.exists("Salary Structure", ss_name):
			frappe.get_doc({
				"doctype": "Salary Structure",
				"name": ss_name,
				"company": self.company,
				"is_active": "Yes",
				"earnings": [{"salary_component": "Basic Salary", "amount": 60000}],
				"deductions": [{"salary_component": "Late Arrival Deduction"}],
			}).insert(ignore_permissions=True)

		ssa = frappe.get_doc({
			"doctype": "Salary Structure Assignment",
			"employee": employee,
			"salary_structure": ss_name,
			"from_date": from_date,
			"base": base,
			"company": self.company,
			"docstatus": 1,
		}).insert(ignore_permissions=True)
		return ssa.name

	def allocate_leave(self, employee, leave_type, days=15):
		year = getdate(today()).year
		from_d = f"{year}-01-01"
		to_d = f"{year}-12-31"

		existing = frappe.get_all(
			"Leave Allocation",
			filters={"employee": employee, "leave_type": leave_type},
			pluck="name",
		)
		for name in existing:
			doc = frappe.get_doc("Leave Allocation", name)
			if doc.docstatus == 1:
				doc.cancel()
			doc.delete()

		la = frappe.get_doc({
			"doctype": "Leave Allocation",
			"employee": employee,
			"leave_type": leave_type,
			"from_date": from_d,
			"to_date": to_d,
			"new_leaves_allocated": days,
			"docstatus": 1,
		}).insert(ignore_permissions=True)
		return la.name

	# ==========================================
	# 1. GRADE BOUNDARIES TESTS
	# ==========================================
	def test_grade_boundaries(self):
		s = settings()
		test_matrix = [
			(dtime(8, 59, 59), None, 0.0),
			(dtime(9, 0, 0), None, 0.0),
			(dtime(9, 0, 1), "Grade 1", 0.166667),
			(dtime(10, 0, 0), "Grade 1", 0.166667),
			(dtime(10, 0, 1), "Grade 2", 0.333333),
			(dtime(11, 0, 0), "Grade 2", 0.333333),
			(dtime(11, 0, 1), "Grade 3", 0.5),
			(dtime(13, 29, 59), "Grade 3", 0.5),
			(dtime(13, 30, 0), "Grade 3", 1.0),
		]
		for arrival_time, expected_grade, expected_days in test_matrix:
			grade, days = get_grade(arrival_time, s)
			self.assertEqual(grade, expected_grade, f"Failed grade check for {arrival_time}")
			self.assertAlmostEqual(days, expected_days, places=4, msg=f"Failed days check for {arrival_time}")

	# ==========================================
	# 2. SETTINGS VALIDATION TESTS (FIX 5)
	# ==========================================
	def test_settings_validation_fractions(self):
		s = frappe.get_single("Attendance Policy Settings")
		s.grade1_deduction = -0.1
		self.assertRaises(frappe.ValidationError, s.save)
		s.reload()

		s.full_day_deduction = 1.5
		self.assertRaises(frappe.ValidationError, s.save)
		s.reload()

	def test_settings_validation_timings(self):
		s = frappe.get_single("Attendance Policy Settings")
		# Non sequential: grade1 ends after grade2
		s.grade1_end = "11:30:00"
		s.grade2_end = "11:00:00"
		self.assertRaises(frappe.ValidationError, s.save)
		s.reload()

	def test_settings_validation_leave_types(self):
		s = frappe.get_single("Attendance Policy Settings")
		s.annual_leave_type = s.casual_leave_type
		self.assertRaises(frappe.ValidationError, s.save)
		s.reload()

	def test_settings_validation_je_accounts(self):
		s = frappe.get_single("Attendance Policy Settings")
		s.create_journal_entry = 1
		s.je_debit_account = None
		self.assertRaises(frappe.ValidationError, s.save)
		s.reload()

	def test_settings_validation_recipients(self):
		s = frappe.get_single("Attendance Policy Settings")
		s.report_recipients = "invalid-email-address, user@"
		self.assertRaises(frappe.ValidationError, s.save)
		s.reload()

	# ==========================================
	# 3. DAILY JOB, IN/OUT & IDEMPOTENCY (FIX 9)
	# ==========================================
	def test_daily_job_in_out_and_idempotency(self):
		emp = self.create_employee("DailyCheckin")
		test_date = "2026-11-04"  # Wednesday

		frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee=%s", emp)
		frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee=%s", emp)
		frappe.db.commit()

		# Add 3 checkins: OUT at 09:10, IN at 09:15, OUT at 17:30
		frappe.get_doc({"doctype": "Employee Checkin", "employee": emp, "time": f"{test_date} 09:10:00", "log_type": "OUT"}).insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "Employee Checkin", "employee": emp, "time": f"{test_date} 09:15:00", "log_type": "IN"}).insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "Employee Checkin", "employee": emp, "time": f"{test_date} 17:30:00", "log_type": "OUT"}).insert(ignore_permissions=True)
		frappe.db.commit()

		daily_job(date=test_date)
		logs = frappe.get_all("Late Arrival Log", filters={"employee": emp, "attendance_date": test_date}, fields=["*"])
		self.assertEqual(len(logs), 1)
		self.assertEqual(logs[0].grade, "Grade 1")
		self.assertIn(str(logs[0].arrival_time), ["09:15:00", "9:15:00"])
		self.assertIn(str(logs[0].exit_time), ["17:30:00"])

		# Idempotency check: run again
		daily_job(date=test_date)
		logs_after = frappe.get_all("Late Arrival Log", filters={"employee": emp, "attendance_date": test_date})
		self.assertEqual(len(logs_after), 1)

	def test_daily_job_skip_joining_and_relieving(self):
		test_date = "2026-11-04"
		# Employee joined AFTER test_date
		emp_future = self.create_employee("FutureHire", joining_date="2026-12-01")
		frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee=%s", emp_future)
		frappe.get_doc({"doctype": "Employee Checkin", "employee": emp_future, "time": f"{test_date} 09:30:00", "log_type": "IN"}).insert(ignore_permissions=True)

		# Employee relieved BEFORE test_date
		emp_relieved = self.create_employee("RelievedEmp", joining_date="2025-01-01", relieving_date="2026-10-01", status="Left")
		frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee=%s", emp_relieved)
		frappe.get_doc({"doctype": "Employee Checkin", "employee": emp_relieved, "time": f"{test_date} 09:30:00", "log_type": "IN"}).insert(ignore_permissions=True)
		frappe.db.commit()

		daily_job(date=test_date)
		self.assertFalse(frappe.db.exists("Late Arrival Log", {"employee": emp_future, "attendance_date": test_date}))
		self.assertFalse(frappe.db.exists("Late Arrival Log", {"employee": emp_relieved, "attendance_date": test_date}))

	def test_daily_job_with_skip_auto_attendance_biometric(self):
		emp = self.create_employee("BiometricZK")
		test_date = "2026-11-04"

		frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee=%s", emp)
		frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee=%s", emp)
		frappe.db.commit()

		# Checkin created like zkteco_sync (skip_auto_attendance = 1)
		frappe.get_doc({
			"doctype": "Employee Checkin",
			"employee": emp,
			"time": f"{test_date} 09:20:00",
			"log_type": "IN",
			"skip_auto_attendance": 1,
			"device_id": "192.168.20.2",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		s = frappe.get_single("Attendance Policy Settings")
		s.include_skip_auto_attendance_checkins = 1
		s.save(ignore_permissions=True)

		daily_job(date=test_date)
		logs = frappe.get_all("Late Arrival Log", filters={"employee": emp, "attendance_date": test_date}, fields=["*"])
		self.assertEqual(len(logs), 1, "Biometric checkin with skip_auto_attendance=1 must be processed when setting is ON")
		self.assertEqual(logs[0].grade, "Grade 1")

		# If setting is disabled, checkins with skip_auto_attendance=1 should be excluded
		frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee=%s", emp)
		frappe.db.commit()
		s.include_skip_auto_attendance_checkins = 0
		s.save(ignore_permissions=True)

		daily_job(date=test_date)
		logs_disabled = frappe.get_all("Late Arrival Log", filters={"employee": emp, "attendance_date": test_date})
		self.assertEqual(len(logs_disabled), 0, "Biometric checkin with skip_auto_attendance=1 must be ignored when setting is OFF")

		# Reset setting back to 1
		s.include_skip_auto_attendance_checkins = 1
		s.save(ignore_permissions=True)

	def test_exempt_employee_bypass(self):
		emp = self.create_employee("ExemptUser")
		test_date = "2026-11-04"

		frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee=%s", emp)
		frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee=%s", emp)
		frappe.db.commit()

		# Add to exempt employees list
		s = frappe.get_single("Attendance Policy Settings")
		s.append("exempt_employees", {
			"employee": emp,
			"reason": "Executive Director",
		})
		s.save(ignore_permissions=True)

		# Employee punches in late at 10:15 (normally Grade 2, 0.3333 days)
		frappe.get_doc({
			"doctype": "Employee Checkin",
			"employee": emp,
			"time": f"{test_date} 10:15:00",
			"log_type": "IN",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		# Run daily job
		daily_job(date=test_date)

		# Assert NO Late Arrival Log was created
		self.assertFalse(
			frappe.db.exists("Late Arrival Log", {"employee": emp, "attendance_date": test_date}),
			"Exempt employee must NOT have a Late Arrival Log generated."
		)

		# Cleanup exempt row
		s.exempt_employees = [r for r in s.exempt_employees if r.employee != emp]
		s.save(ignore_permissions=True)

	# ==========================================
	# 4. HR NOTIFICATION (FIX 4)
	# ==========================================
	def test_hr_notification_creation_and_dedupe(self):
		emp = self.create_employee("NotifyTest")
		test_date = "2026-11-05"
		frappe.db.sql("DELETE FROM `tabEmployee Checkin` WHERE employee=%s", emp)
		frappe.db.commit()
		frappe.get_doc({"doctype": "Employee Checkin", "employee": emp, "time": f"{test_date} 09:30:00", "log_type": "IN"}).insert(ignore_permissions=True)
		frappe.db.commit()

		# Run daily job
		daily_job(date=test_date)
		subject = f"Daily Attendance Summary - {test_date}"

		notifs = frappe.get_all("Notification Log", filters={"subject": subject})
		self.assertGreaterEqual(len(notifs), 1)

		# Re-running daily job does not duplicate notifications
		count_before = len(notifs)
		daily_job(date=test_date)
		count_after = frappe.db.count("Notification Log", {"subject": subject})
		self.assertEqual(count_before, count_after)

	# ==========================================
	# 5. CASUAL LEAVE ENCASHMENT CAP (FIX 2)
	# ==========================================
	def test_casual_leave_encashment_cap(self):
		emp = self.create_employee("EncashTest")
		frappe.db.sql("DELETE FROM `tabLeave Encashment` WHERE employee=%s", emp)
		frappe.db.commit()
		self.assign_salary(emp)
		self.allocate_leave(emp, self.casual_lt, 15)

		# 10 days encashment allowed
		enc1 = frappe.get_doc({
			"doctype": "Leave Encashment",
			"employee": emp,
			"leave_type": self.casual_lt,
			"leave_period": self.leave_period,
			"encashment_date": "2026-05-10",
			"encashment_days": 10,
		})
		enc1.insert(ignore_permissions=True)
		self.assertTrue(enc1.name)

		# Trying 11 days encashment must be blocked
		enc_fail = frappe.get_doc({
			"doctype": "Leave Encashment",
			"employee": emp,
			"leave_type": self.casual_lt,
			"leave_period": self.leave_period,
			"encashment_date": "2026-05-11",
			"encashment_days": 11,
		})
		self.assertRaises(frappe.ValidationError, enc_fail.insert)

		# Clean up enc1
		frappe.delete_doc("Leave Encashment", enc1.name, force=True)

	# ==========================================
	# 6. ADJACENT HOLIDAY LEAVE RULES (FIX 1)
	# ==========================================
	def test_adjacent_holiday_chain_and_ledger(self):
		emp = self.create_employee("AdjHolsTest")
		for att in frappe.get_all("Attendance", filters={"employee": emp}, pluck="name"):
			try:
				doc = frappe.get_doc("Attendance", att)
				if doc.docstatus == 1:
					doc.cancel()
				doc.delete()
			except Exception:
				pass
		for name in frappe.get_all("Leave Application", filters={"employee": emp}, pluck="name"):
			try:
				doc = frappe.get_doc("Leave Application", name)
				if doc.docstatus == 1:
					doc.cancel()
				doc.delete()
			except Exception:
				pass
		self.allocate_leave(emp, self.casual_lt, 15)

		# Leave on Monday 2026-10-19 (Sunday 2026-10-18 was off)
		# Case A: With Reason -> No extra ledger entries
		la_reason = frappe.get_doc({
			"doctype": "Leave Application",
			"employee": emp,
			"leave_type": self.casual_lt,
			"from_date": "2026-10-19",
			"to_date": "2026-10-19",
			"description": "Valid family emergency justification",
			"status": "Approved",
			"leave_approver": "Administrator",
			"company": self.company,
		})
		la_reason.insert(ignore_permissions=True)
		la_reason.submit()

		# Case B: Without Reason -> Extra ledger entry for Sunday
		la_no_reason = frappe.get_doc({
			"doctype": "Leave Application",
			"employee": emp,
			"leave_type": self.casual_lt,
			"from_date": "2026-10-26",
			"to_date": "2026-10-26",
			"description": "",
			"status": "Approved",
			"leave_approver": "Administrator",
			"company": self.company,
		})
		la_no_reason.insert(ignore_permissions=True)
		la_no_reason.submit()

		# Verify extra ledger entry exists
		entries = frappe.get_all(
			"Leave Ledger Entry",
			filters={"transaction_name": la_no_reason.name},
			fields=["name", "leaves", "from_date"],
		)
		self.assertEqual(len(entries), 2)  # 1 for leave day + 1 for adjacent Sunday

		# Cancel la_no_reason -> both ledger entries reversed/deleted
		la_no_reason.cancel()
		remaining = frappe.get_all("Leave Ledger Entry", filters={"transaction_name": la_no_reason.name})
		self.assertEqual(len(remaining), 0)

	# ==========================================
	# 7. ANNUAL LEAVE RULES
	# ==========================================
	def test_annual_leave_rules(self):
		emp_new = self.create_employee("AnnualNew", joining_date="2026-06-01")
		emp_ok = self.create_employee("AnnualOk", joining_date="2024-01-01")
		for name in frappe.get_all("Leave Application", filters={"employee": ["in", [emp_new, emp_ok]]}, pluck="name"):
			doc = frappe.get_doc("Leave Application", name)
			if doc.docstatus == 1:
				doc.cancel()
			doc.delete()
		self.allocate_leave(emp_ok, self.annual_lt, 15)

		# Less than 12 months service blocked
		la_fail = frappe.get_doc({
			"doctype": "Leave Application",
			"employee": emp_new,
			"leave_type": self.annual_lt,
			"from_date": "2026-11-20",
			"to_date": "2026-11-22",
			"leave_approver": "Administrator",
			"company": self.company,
		})
		self.assertRaises(frappe.ValidationError, la_fail.insert)

		# Eligible employee
		self.allocate_leave(emp_ok, self.annual_lt, 15)
		la_ok = frappe.get_doc({
			"doctype": "Leave Application",
			"employee": emp_ok,
			"leave_type": self.annual_lt,
			"from_date": "2026-12-10",
			"to_date": "2026-12-12",
			"status": "Approved",
			"leave_approver": "Administrator",
			"company": self.company,
		})
		la_ok.insert(ignore_permissions=True)
		self.assertTrue(la_ok.name)

	# ==========================================
	# 8. STALE LOGS & MONTH-END SPLIT (FIX 7 & 6)
	# ==========================================
	def test_month_end_stale_logs_and_dry_run(self):
		emp = self.create_employee("StaleLogEmp")
		for ads in frappe.get_all("Additional Salary", filters={"employee": emp}, pluck="name"):
			try:
				doc = frappe.get_doc("Additional Salary", ads)
				if doc.docstatus == 1:
					doc.cancel()
				doc.delete()
			except Exception:
				pass
		for lde in frappe.get_all("Late Deduction Entry", filters={"employee": emp}, pluck="name"):
			try:
				doc = frappe.get_doc("Late Deduction Entry", lde)
				if doc.docstatus == 1:
					doc.cancel()
				doc.delete()
			except Exception:
				pass
		self.assign_salary(emp, base=60000)
		self.allocate_leave(emp, self.casual_lt, 0.2)  # 0.2 balance

		frappe.db.sql("DELETE FROM `tabLate Arrival Log` WHERE employee=%s", emp)
		frappe.db.commit()

		# Stale pending log from previous month (Sep) + current month log (Oct)
		frappe.get_doc({
			"doctype": "Late Arrival Log",
			"employee": emp,
			"attendance_date": "2026-09-25",
			"arrival_time": "10:30:00",
			"grade": "Grade 2",
			"deduction_days": 0.333333,
			"status": "Pending",
		}).insert(ignore_permissions=True)

		frappe.get_doc({
			"doctype": "Late Arrival Log",
			"employee": emp,
			"attendance_date": "2026-10-15",
			"arrival_time": "11:30:00",
			"grade": "Grade 3",
			"deduction_days": 0.5,
			"status": "Pending",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		# 1. Test Dry Run produces no DB writes
		res_dry = process_month_end(period_end="2026-10-31", dry_run=True)
		self.assertTrue(res_dry["dry_run"])
		matching = [d for d in res_dry["details"] if d["employee"] == emp]
		self.assertEqual(len(matching), 1)
		self.assertEqual(matching[0]["late_days"], 0.8333)
		self.assertEqual(matching[0]["from_leave"], 0.2)
		self.assertEqual(matching[0]["from_salary"], 0.6333)
		self.assertEqual(matching[0]["logs"], 2)

		# Logs must still be Pending
		pending_count = frappe.db.count("Late Arrival Log", {"employee": emp, "status": "Pending"})
		self.assertEqual(pending_count, 2)

		# 2. Test Real Month-End Execution
		res_real = process_month_end(period_end="2026-10-31", dry_run=False)
		self.assertFalse(res_real["dry_run"])
		# Both logs must now be Processed
		processed_count = frappe.db.count("Late Arrival Log", {"employee": emp, "status": "Processed"})
		self.assertEqual(processed_count, 2)

		# Verify Late Deduction Entry recorded both dates
		entry = frappe.get_last_doc("Late Deduction Entry", filters={"employee": emp})
		self.assertIn("2026-09-25", entry.included_periods)
		self.assertIn("2026-10-15", entry.included_periods)
		self.assertEqual(flt(entry.from_leave), 0.2)
		self.assertAlmostEqual(flt(entry.from_salary), 0.6333, places=2)

	# ==========================================
	# 9. PERMISSIONS TESTS
	# ==========================================
	def test_plain_employee_permissions(self):
		user_email = "tap_plain_employee@example.com"
		if not frappe.db.exists("User", user_email):
			user = frappe.get_doc({
				"doctype": "User",
				"email": user_email,
				"first_name": "Plain",
				"roles": [{"role": "Employee"}],
			}).insert(ignore_permissions=True)

		frappe.set_user(user_email)
		# Employee cannot read Settings or Late Arrival Log
		self.assertFalse(frappe.has_permission("Attendance Policy Settings", "read"))
		self.assertFalse(frappe.has_permission("Late Arrival Log", "write"))
		frappe.set_user("Administrator")
