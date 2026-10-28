#!/usr/bin/env python3
"""
Test script for Attendance Policy app
Run from bench: bench --site YOUR_SITE execute attendance_policy.test_setup
"""

import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate, today, get_first_day, get_last_day


def test_setup():
	"""Create test data and run all tests"""
	print("\n" + "="*60)
	print("ATTENDANCE POLICY TEST SUITE")
	print("="*60)
	
	# Check if app is installed
	if "attendance_policy" not in frappe.get_installed_apps():
		print("❌ App not installed. Run: bench --site YOUR_SITE install-app attendance_policy")
		return
	
	print("✅ App is installed")
	
	# Check settings
	try:
		settings = frappe.get_single("Attendance Policy Settings")
		print(f"✅ Settings exist: {settings.name}")
		if not settings.casual_leave_type:
			print("⚠️  Casual Leave Type not configured in settings")
		if not settings.report_recipients:
			print("⚠️  Report recipients not configured in settings")
	except Exception as e:
		print(f"❌ Settings error: {e}")
		return
	
	# Check salary component
	if frappe.db.exists("Salary Component", "Late Arrival Deduction"):
		print("✅ Salary Component 'Late Arrival Deduction' exists")
	else:
		print("❌ Salary Component 'Late Arrival Deduction' missing")
	
	# Check dashboard
	if frappe.db.exists("Dashboard", "Late Arrivals"):
		print("✅ Dashboard 'Late Arrivals' created")
	else:
		print("⚠️  Dashboard not found (may need manual creation)")
	
	# Check reports
	reports = ["Daily Attendance Summary", "Habitual Late Comers"]
	for r in reports:
		if frappe.db.exists("Report", r):
			print(f"✅ Report '{r}' exists")
		else:
			print(f"❌ Report '{r}' missing")
	
	# Test grading logic
	print("\n" + "-"*60)
	print("Testing grading boundaries...")
	print("-"*60)
	test_grading()
	
	# Offer to create demo data
	print("\n" + "-"*60)
	print("To create demo data with test employees and check-ins:")
	print("  bench --site YOUR_SITE execute attendance_policy.test_setup.create_demo_data")
	print("\nTo test daily job on today:")
	print("  bench --site YOUR_SITE execute attendance_policy.tasks.daily_job")
	print("\nTo test month-end (dry run):")
	print("  bench --site YOUR_SITE execute attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end --kwargs \"{'period_end':'YYYY-MM-DD','dry_run':True}\"")
	print("-"*60)


def test_grading():
	"""Test the grading function"""
	from datetime import time as dtime
	from attendance_policy.tasks import get_grade
	
	settings = frappe._dict({
		"arrival_cutoff": "09:00:00",
		"grade1_end": "10:00:00",
		"grade2_end": "11:00:00",
		"second_half_cutoff": "13:30:00",
		"grade1_deduction": 0.166667,
		"grade2_deduction": 0.333333,
		"grade3_deduction": 0.5,
		"full_day_deduction": 1.0
	})
	
	tests = [
		(dtime(8, 30), None, 0, "8:30 AM - On time"),
		(dtime(9, 0), None, 0, "9:00 AM - Exactly on time"),
		(dtime(9, 1), "Grade 1", 0.166667, "9:01 AM - Grade 1"),
		(dtime(9, 30), "Grade 1", 0.166667, "9:30 AM - Grade 1"),
		(dtime(10, 0), "Grade 1", 0.166667, "10:00 AM - Grade 1 boundary"),
		(dtime(10, 1), "Grade 2", 0.333333, "10:01 AM - Grade 2"),
		(dtime(10, 30), "Grade 2", 0.333333, "10:30 AM - Grade 2"),
		(dtime(11, 0), "Grade 2", 0.333333, "11:00 AM - Grade 2 boundary"),
		(dtime(11, 1), "Grade 3", 0.5, "11:01 AM - Grade 3 (half day)"),
		(dtime(13, 29), "Grade 3", 0.5, "1:29 PM - Grade 3 (half day)"),
		(dtime(13, 30), "Grade 3", 1.0, "1:30 PM - Full day"),
		(dtime(14, 0), "Grade 3", 1.0, "2:00 PM - Full day"),
	]
	
	all_pass = True
	for time_val, expected_grade, expected_days, desc in tests:
		grade, days = get_grade(time_val, settings)
		if grade == expected_grade and abs(days - expected_days) < 0.0001:
			print(f"  ✅ {desc}")
		else:
			print(f"  ❌ {desc} - Got {grade}, {days:.4f}")
			all_pass = False
	
	if all_pass:
		print("\n✅ All grading tests passed!")
	else:
		print("\n❌ Some grading tests failed")


def create_demo_data():
	"""Create demo employees and check-ins for testing"""
	print("\n" + "="*60)
	print("CREATING DEMO DATA")
	print("="*60)
	
	frappe.set_user("Administrator")
	
	# Get or create company
	company = frappe.db.get_value("Company", {}, "name") or "Test Company"
	
	# Create test employees
	employees = []
	for i in range(1, 4):
		emp_id = f"TEST-EMP-{i:03d}"
		if frappe.db.exists("Employee", emp_id):
			print(f"⏭️  Employee {emp_id} already exists")
			employees.append(emp_id)
			continue
		
		emp = frappe.get_doc({
			"doctype": "Employee",
			"employee": emp_id,
			"first_name": f"Test",
			"last_name": f"Employee{i}",
			"company": company,
			"date_of_joining": "2024-01-01",
			"status": "Active",
			"gender": "Male"
		})
		emp.insert(ignore_permissions=True)
		employees.append(emp.name)
		print(f"✅ Created employee: {emp.name} - {emp.employee_name}")
	
	# Create check-ins for today with different grades
	test_date = getdate(today())
	checkin_times = [
		(employees[0], datetime.combine(test_date, datetime.strptime("09:15", "%H:%M").time()), "Grade 1"),
		(employees[0], datetime.combine(test_date, datetime.strptime("17:30", "%H:%M").time()), "Exit"),
		(employees[1], datetime.combine(test_date, datetime.strptime("10:30", "%H:%M").time()), "Grade 2"),
		(employees[1], datetime.combine(test_date, datetime.strptime("18:00", "%H:%M").time()), "Exit"),
		(employees[2], datetime.combine(test_date, datetime.strptime("11:30", "%H:%M").time()), "Grade 3"),
		(employees[2], datetime.combine(test_date, datetime.strptime("17:45", "%H:%M").time()), "Exit"),
	]
	
	for emp, time_val, label in checkin_times:
		# Check if already exists
		if frappe.db.exists("Employee Checkin", {"employee": emp, "time": time_val}):
			continue
		
		checkin = frappe.get_doc({
			"doctype": "Employee Checkin",
			"employee": emp,
			"time": time_val
		})
		checkin.insert(ignore_permissions=True)
		print(f"✅ Created check-in: {emp} at {time_val.strftime('%H:%M')} ({label})")
	
	frappe.db.commit()
	
	print("\n" + "-"*60)
	print(f"Demo data created for {len(employees)} employees")
	print(f"Check-ins created for date: {test_date}")
	print("\nNext steps:")
	print(f"1. Run daily job: bench --site YOUR_SITE execute attendance_policy.tasks.daily_job --kwargs \"{{\'date\':'{test_date}'}}\"")
	print("2. Check Late Arrival Log list view")
	print("3. View Daily Attendance Summary report")
	print("-"*60)


def cleanup_demo_data():
	"""Remove all demo data"""
	print("\n" + "="*60)
	print("CLEANING UP DEMO DATA")
	print("="*60)
	
	frappe.set_user("Administrator")
	
	# Delete test employees and related records
	test_emps = frappe.get_all("Employee", filters={"employee": ["like", "TEST-EMP-%"]}, pluck="name")
	
	for emp in test_emps:
		# Delete related records
		for dt in ["Employee Checkin", "Late Arrival Log", "Late Deduction Entry"]:
			records = frappe.get_all(dt, filters={"employee": emp}, pluck="name")
			for rec in records:
				frappe.delete_doc(dt, rec, force=True)
		
		frappe.delete_doc("Employee", emp, force=True)
		print(f"✅ Deleted employee: {emp}")
	
	frappe.db.commit()
	print(f"\n✅ Cleanup complete: {len(test_emps)} test employees removed")


if __name__ == "__main__":
	test_setup()
