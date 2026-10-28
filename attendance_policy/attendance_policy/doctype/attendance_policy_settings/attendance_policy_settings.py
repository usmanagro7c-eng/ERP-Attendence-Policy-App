import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, getdate


class AttendancePolicySettings(Document):
	pass


@frappe.whitelist()
def process_month_end(period_end, dry_run=False):
	"""Manually trigger month-end processing for a given date.
	period_end: YYYY-MM-DD (should be last day of month)
	dry_run: if True, return preview without committing
	"""
	from attendance_policy.tasks import process_employee, settings
	
	period_end = getdate(period_end)
	if period_end != get_last_day(period_end):
		frappe.throw(_("Period end must be the last day of the month"))
	
	s = settings()
	month_start = get_first_day(period_end)
	
	# Get pending logs for the month
	logs = frappe.get_all(
		"Late Arrival Log",
		filters={
			"status": "Pending",
			"attendance_date": ["between", [month_start, period_end]]
		},
		fields=["name", "employee", "employee_name", "deduction_days"]
	)
	
	# Group by employee
	by_emp = {}
	for l in logs:
		by_emp.setdefault(l.employee, []).append(l)
	
	results = []
	for emp, ls in by_emp.items():
		total = sum(frappe.utils.flt(l.deduction_days) for l in ls)
		emp_name = ls[0].employee_name
		
		if dry_run:
			results.append({
				"employee": emp,
				"employee_name": emp_name,
				"late_days": total,
				"logs": len(ls)
			})
		else:
			try:
				process_employee(emp, ls, period_end, s)
				frappe.db.commit()
				results.append({
					"employee": emp,
					"employee_name": emp_name,
					"status": "Success",
					"late_days": total
				})
			except Exception as e:
				frappe.db.rollback()
				frappe.log_error(title=f"Month-end failed: {emp}")
				results.append({
					"employee": emp,
					"employee_name": emp_name,
					"status": "Failed",
					"error": str(e)
				})
	
	return {
		"period_end": str(period_end),
		"dry_run": bool(dry_run),
		"employees_processed": len(results),
		"details": results
	}
