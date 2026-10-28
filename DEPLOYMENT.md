# DEPLOYMENT CHECKLIST

## Pre-Installation

- [ ] Frappe v16 bench with ERPNext v16 and HRMS v16 installed
- [ ] Python 3.10+ available
- [ ] MariaDB/MySQL running
- [ ] Site created and accessible

## Installation Steps

```bash
# 1. Get the app
cd /path/to/frappe-bench
bench get-app /path/to/attendance_policy

# 2. Install on site
bench --site YOUR_SITE install-app attendance_policy

# 3. Run migrations
bench --site YOUR_SITE migrate

# 4. Verify installation
bench --site YOUR_SITE execute attendance_policy.verify_installation

# 5. Optional: Create demo data for testing
bench --site YOUR_SITE execute attendance_policy.test_setup.create_demo_data
```

## Post-Installation Configuration

### 1. Attendance Policy Settings
Navigate to: **Attendance Policy workspace → Attendance Policy Settings**

Configure:
- [ ] Company: Select your company
- [ ] Timings: Verify defaults (09:00 cutoff, Grade 1 ends 10:00, Grade 2 ends 11:00, full-day 13:30)
- [ ] Deduction fractions: Verify (1/6, 1/3, 1/2, 1 full day)
- [ ] Habitual threshold: Set min late count (default 3)
- [ ] Report recipients: Add email addresses (comma or newline separated)
- [ ] Casual Leave Type: Link to your Leave Type
- [ ] Annual Leave Type: Link to your Leave Type
- [ ] Max consecutive casual days: Set to 3
- [ ] Enable "Deduct from leave balance first"
- [ ] Salary component: Verify "Late Arrival Deduction" is set
- [ ] Salary days divisor: Set to 30 (or 26 for working days)
- [ ] Journal Entry: Leave OFF unless specifically required

### 2. Leave Types (if not exists)
Navigate to: **HR → Leave Type**

Create two leave types:

**Casual/Sick Leave:**
- [ ] Leave Type Name: Casual Leave
- [ ] Max Continuous Days Applicable: 3
- [ ] Allow Encashment: Yes
- [ ] Encashment Threshold Days: 10
- [ ] Include holidays within leaves: Configure per policy
- [ ] Is Carry Forward: As per policy

**Annual Leave:**
- [ ] Leave Type Name: Annual Leave
- [ ] Is Earned Leave: Yes (after 12 months)
- [ ] Include holidays within leaves: Yes
- [ ] Max Leaves Allowed: 15

### 3. Leave Policy
Navigate to: **HR → Leave Policy**

- [ ] Create policy with:
  - Casual Leave: 15 days
  - Annual Leave: 15 days (earned after 12 months)
- [ ] Effective from: Start of year

### 4. Leave Allocations
Navigate to: **HR → Leave Allocation**

- [ ] Create allocations for all active employees
- [ ] Link to Leave Policy
- [ ] Set period (annual)

### 5. Holiday List
Navigate to: **HR → Holiday List**

- [ ] Create company holiday list
- [ ] Add all Sundays as weekly off
- [ ] Add gazetted holidays
- [ ] Assign to company or individual employees

### 6. Shift Types
Navigate to: **HR → Shift Type**

Create shifts:

**Regular Shift (Mon-Thu, Sat):**
- [ ] Name: Regular Shift
- [ ] Start Time: 08:30
- [ ] End Time: 17:30
- [ ] Working Hours: 8
- [ ] Enable Auto Attendance: Yes

**Friday Shift:**
- [ ] Name: Friday Shift
- [ ] Start Time: 08:30
- [ ] End Time: 16:30
- [ ] Working Hours: 7
- [ ] Enable Auto Attendance: Yes

### 7. Shift Assignments
Navigate to: **HR → Shift Assignment**

- [ ] Assign employees to appropriate shifts
- [ ] Set effective dates

### 8. Salary Structure
Navigate to: **Payroll → Salary Structure**

- [ ] Verify "Late Arrival Deduction" appears in deductions list
- [ ] Configure salary structures for employees
- [ ] Create Salary Structure Assignments

### 9. Email Configuration
Navigate to: **Setup → Email Account**

- [ ] Configure outgoing email (SMTP)
- [ ] Test email sending
- [ ] Verify recipients can receive emails

### 10. Scheduler
Check scheduler is running:

```bash
bench --site YOUR_SITE doctor
# Ensure "Scheduler: Active" is shown

# If disabled, enable it:
bench --site YOUR_SITE set-config disable_scheduler 0
bench restart
```

## Testing

### 1. Unit Tests
```bash
# Run all tests
bench --site YOUR_SITE run-tests --app attendance_policy

# Run specific test
bench --site YOUR_SITE run-tests --app attendance_policy --module attendance_policy.tests.test_late_grading
```

### 2. Daily Job Test
```bash
# Create demo data first
bench --site YOUR_SITE execute attendance_policy.test_setup.create_demo_data

# Run daily job for today
bench --site YOUR_SITE execute attendance_policy.tasks.daily_job

# Or for specific date
bench --site YOUR_SITE execute attendance_policy.tasks.daily_job --kwargs "{'date':'2026-10-28'}"

# Check results:
# 1. Go to Late Arrival Log list - verify logs created
# 2. Check email inbox for daily report
# 3. View Daily Attendance Summary report
```

### 3. Leave Validation Test
Navigate to: **HR → Leave Application**

Test scenarios:
- [ ] Casual leave > 3 days → Should block
- [ ] Casual leave adjacent to Sunday without reason → Should warn
- [ ] Annual leave for new employee (< 12 months) → Should block
- [ ] Annual leave for past date (non-HR Manager) → Should block
- [ ] Third annual leave part in same year → Should block

### 4. Month-End Test
```bash
# Preview first (dry run)
bench --site YOUR_SITE execute attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end --kwargs "{'period_end':'2026-10-31','dry_run':True}"

# Review output, then run actual processing
bench --site YOUR_SITE execute attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end --kwargs "{'period_end':'2026-10-31','dry_run':False}"

# Verify results:
# 1. Check Late Deduction Entry created
# 2. Check Leave Ledger Entry (if balance available)
# 3. Check Additional Salary created
# 4. Logs marked as Processed
```

### 5. Salary Slip Test
Navigate to: **Payroll → Salary Slip**

- [ ] Create salary slip for employee with late deductions
- [ ] Verify "Late Arrival Deduction" appears in deductions
- [ ] Verify amount is correct (base/30 × days)
- [ ] Submit and check net pay

### 6. Reports Test
Navigate to: **Attendance Policy workspace → Reports**

- [ ] Open Daily Attendance Summary
  - Select date
  - Verify check-in/out times
  - Verify late grades
- [ ] Open Habitual Late Comers
  - Set date range
  - Verify late count by grade
  - Check chart displays

### 7. Dashboard Test
Navigate to: **Attendance Policy workspace → Late Arrivals Dashboard**

- [ ] Verify all 3 charts load
- [ ] Charts show data correctly
- [ ] Charts update after running daily job

## Production Deployment

### Scheduler Configuration
The app runs two scheduled jobs:

**Daily Job (9:00 PM):**
- Grades late arrivals
- Sends email report
- To change timing, edit `hooks.py`:
```python
"cron": {
    "0 21 * * *": ["attendance_policy.tasks.daily_job"],  # 21 = 9 PM
}
```

**Month-End Job (11:30 PM):**
- Processes deductions on last day of month
- To change timing, edit `hooks.py`:
```python
"cron": {
    "30 23 * * *": ["attendance_policy.tasks.month_end_job"],  # 23:30 = 11:30 PM
}
```

After editing hooks:
```bash
bench --site YOUR_SITE migrate
bench restart
```

### Monitoring

Check logs regularly:
```bash
# Error log
tail -f logs/error.log

# Scheduled job log
grep "attendance_policy.tasks" logs/scheduler.log

# Check late deduction errors
# In desk: System Console → Error Log → filter "Late deduction failed"
```

### Backup Strategy
- [ ] Database backups before month-end processing
- [ ] Regular backups of Late Arrival Log and Late Deduction Entry
- [ ] Test restore procedure

## Maintenance

### Monthly Tasks
- [ ] Review habitual late comers report
- [ ] Verify month-end processing completed
- [ ] Check email delivery
- [ ] Reconcile salary slips with late deductions

### Quarterly Tasks
- [ ] Review and adjust thresholds if needed
- [ ] Check leave balances reconcile
- [ ] Update holiday list for upcoming period

### Annual Tasks
- [ ] Review and update Leave Policy
- [ ] Create new Leave Allocations
- [ ] Update Holiday List for new year

## Troubleshooting

### Daily job not creating logs
1. Check scheduler is running: `bench --site YOUR_SITE doctor`
2. Check Employee Checkin records exist for the date
3. Verify employees are Active status
4. Check error log: `tail -f logs/error.log`

### Emails not sending
1. Verify Email Account configured
2. Check report_recipients in Settings
3. Check Email Queue: Setup → Email Queue
4. Test email: `bench --site YOUR_SITE send-email --email your@email.com`

### Month-end not deducting
1. Verify Late Arrival Logs exist with status "Pending"
2. Check Salary Structure Assignment exists for employees
3. Verify casual leave balance: use console to call `get_leave_balance_on()`
4. Check error log for specific employee failures

### Leave validation not working
1. Verify leave types match Settings exactly (case-sensitive)
2. Check doc_events registered: `bench --site YOUR_SITE migrate`
3. Test manually in Leave Application form

## Support Contacts

For issues:
1. Check README.md for known limitations
2. Review error logs
3. Test with `verify_installation.py`
4. Create GitHub issue with logs and steps to reproduce

## Cleanup (for testing only)

Remove demo data:
```bash
bench --site YOUR_SITE execute attendance_policy.test_setup.cleanup_demo_data
```

Uninstall app:
```bash
bench --site YOUR_SITE uninstall-app attendance_policy
bench remove-app attendance_policy
```
