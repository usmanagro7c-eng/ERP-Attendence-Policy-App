#!/usr/bin/env python3
"""
Quick verification script - checks that all components are present
Run: bench --site YOUR_SITE execute attendance_policy.verify_installation
"""

import frappe


def verify_installation():
	"""Verify all app components are installed correctly"""
	print("\n" + "="*70)
	print("ATTENDANCE POLICY - INSTALLATION VERIFICATION")
	print("="*70)
	
	checks = []
	
	# 1. App installed
	if "attendance_policy" in frappe.get_installed_apps():
		checks.append(("✅", "App installed"))
	else:
		checks.append(("❌", "App NOT installed"))
		print_results(checks)
		return
	
	# 2. DocTypes
	doctypes = [
		"Attendance Policy Settings",
		"Late Arrival Log",
		"Late Deduction Entry"
	]
	for dt in doctypes:
		if frappe.db.exists("DocType", dt):
			checks.append(("✅", f"DocType: {dt}"))
		else:
			checks.append(("❌", f"DocType: {dt} MISSING"))
	
	# 3. Reports
	reports = ["Daily Attendance Summary", "Habitual Late Comers"]
	for r in reports:
		if frappe.db.exists("Report", r):
			checks.append(("✅", f"Report: {r}"))
		else:
			checks.append(("❌", f"Report: {r} MISSING"))
	
	# 4. Salary Component
	if frappe.db.exists("Salary Component", "Late Arrival Deduction"):
		checks.append(("✅", "Salary Component: Late Arrival Deduction"))
	else:
		checks.append(("❌", "Salary Component: Late Arrival Deduction MISSING"))
	
	# 5. Dashboard
	if frappe.db.exists("Dashboard", "Late Arrivals"):
		checks.append(("✅", "Dashboard: Late Arrivals"))
	else:
		checks.append(("⚠️", "Dashboard: Late Arrivals (may need manual creation)"))
	
	# 6. Settings configured
	settings = frappe.get_single("Attendance Policy Settings")
	if settings.casual_leave_type:
		checks.append(("✅", f"Casual Leave Type: {settings.casual_leave_type}"))
	else:
		checks.append(("⚠️", "Casual Leave Type: NOT CONFIGURED"))
	
	if settings.annual_leave_type:
		checks.append(("✅", f"Annual Leave Type: {settings.annual_leave_type}"))
	else:
		checks.append(("⚠️", "Annual Leave Type: NOT CONFIGURED"))
	
	if settings.report_recipients:
		checks.append(("✅", f"Email Recipients: {len(settings.report_recipients.split(','))} configured"))
	else:
		checks.append(("⚠️", "Email Recipients: NOT CONFIGURED"))
	
	if settings.company:
		checks.append(("✅", f"Company: {settings.company}"))
	else:
		checks.append(("⚠️", "Company: NOT SET"))
	
	# 7. Scheduler hooks
	from attendance_policy import hooks
	if hasattr(hooks, 'scheduler_events') and hooks.scheduler_events:
		checks.append(("✅", "Scheduler events registered"))
	else:
		checks.append(("❌", "Scheduler events NOT registered"))
	
	# 8. Doc events hooks
	if hasattr(hooks, 'doc_events') and hooks.doc_events:
		checks.append(("✅", "Doc events registered (Leave Application validation)"))
	else:
		checks.append(("❌", "Doc events NOT registered"))
	
	# 9. Module registered
	if frappe.db.exists("Module Def", "Attendance Policy"):
		checks.append(("✅", "Module: Attendance Policy"))
	else:
		checks.append(("⚠️", "Module: Attendance Policy (will be created on migrate)"))
	
	print_results(checks)
	
	# Configuration instructions
	print("\n" + "="*70)
	print("CONFIGURATION REQUIRED (if not done):")
	print("="*70)
	print("""
1. Configure Attendance Policy Settings:
   - Go to: Attendance Policy workspace → Attendance Policy Settings
   - Set Company
   - Link Casual Leave Type (create in Leave Type if needed)
   - Link Annual Leave Type (create in Leave Type if needed)
   - Add email recipients (comma-separated)

2. Setup Leave Types (if not exists):
   - HR → Leave Type → Create "Casual Leave" and "Annual Leave"
   - Configure: max days, encashment, eligibility, etc.

3. Setup Leave Policy and Allocations:
   - HR → Leave Policy → Create policy with 15 Casual + 15 Annual
   - HR → Leave Allocation → Allocate to employees

4. Create Holiday List:
   - HR → Holiday List → Add Sundays + company holidays
   - Assign to company or employees

5. Create Shift Types:
   - HR → Shift Type → Create shifts (Mon-Sat 8h, Friday 7h)
   - Assign to employees

6. Test the installation:
   bench --site YOUR_SITE execute attendance_policy.test_setup

7. Create demo data (optional):
   bench --site YOUR_SITE execute attendance_policy.test_setup.create_demo_data
""")


def print_results(checks):
	"""Print check results"""
	print()
	for status, msg in checks:
		print(f"  {status}  {msg}")
	
	failed = sum(1 for s, _ in checks if s == "❌")
	warnings = sum(1 for s, _ in checks if s == "⚠️")
	passed = sum(1 for s, _ in checks if s == "✅")
	
	print("\n" + "-"*70)
	print(f"Results: {passed} passed, {warnings} warnings, {failed} failed")
	print("-"*70)


if __name__ == "__main__":
	verify_installation()
