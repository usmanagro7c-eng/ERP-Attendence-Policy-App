app_name = "attendance_policy"
app_title = "Attendance Policy"
app_publisher = "Your Company"
app_description = "Attendance and leave policy automation"
app_email = "you@example.com"
app_license = "mit"
required_apps = ["erpnext", "hrms"]

after_install = "attendance_policy.install.after_install"

doc_events = {
	"Leave Application": {"validate": "attendance_policy.leave_rules.validate_leave_application"}
}

scheduler_events = {
	"cron": {
		# daily: grade today's late arrivals + email report
		"0 21 * * *": ["attendance_policy.tasks.daily_job"],
		# runs every night, acts only on the last day of the month
		"30 23 * * *": ["attendance_policy.tasks.month_end_job"],
	}
}
