# Attendance Policy

Complete Frappe custom app for ERPNext v16 + HRMS v16 that enforces company attendance/leave rules, automates late-arrival deductions, sends daily attendance emails, provides late-comer analytics, and posts month-end salary deductions.

## Features

### 🎯 Core Functionality
- **Daily Late Arrival Grading**: Automatically grades employees based on check-in time (Grade 1/2/3)
- **Automated Email Reports**: Daily HTML email with check-in/out times, late arrivals, and habitual offenders
- **Month-End Automation**: Deducts from casual leave first, then creates Additional Salary deductions
- **Leave Policy Validation**: Enforces casual/annual leave rules per company memo
- **Analytics Dashboard**: Charts showing late trends by grade, employee, and time
- **Manual Processing**: Dry-run and manual month-end processing from Settings

### 📊 Grading Rules (Memo Section 3)
- **On Time**: Arrival ≤ 09:00 AM → No deduction
- **Grade 1**: 09:00 to 10:00 AM → 1/6 day leave (0.166667 days)
- **Grade 2**: 10:00 to 11:00 AM → 1/3 day leave (0.333333 days)
- **Grade 3**: 11:00 AM to 01:30 PM → 1/2 day leave (0.5 days)
- **Full Day**: Arrival ≥ 01:30 PM → 1 full day leave

### 📝 Leave Rules (Memo Section 4)
#### Casual/Sick Leave (built-in ERPNext + custom validation)
- 15 days annual entitlement (prorated)
- Max 3 consecutive days
- Adjacent holidays/Sundays count as leave unless justified
- Encashable (max 10 days per year) - *configure in Leave Type*

#### Annual Leave (built-in ERPNext + custom validation)
- 15 days after 12 months continuous service
- Must be applied in advance (HR Manager can override)
- Max 2 parts per calendar year
- Includes Sundays/holidays - *configure in Leave Type*

## Installation

### Prerequisites
- Frappe v16 bench with ERPNext v16 and HRMS v16 installed
- Python 3.10+
- MariaDB/MySQL database

### Install App
```bash
# From your frappe-bench directory
cd frappe-bench

# Get the app (if from git repo)
bench get-app https://github.com/YOUR_USERNAME/attendance_policy.git

# OR if developing locally, link the app
bench get-app /path/to/attendance_policy

# Install on your site
bench --site YOUR_SITE install-app attendance_policy

# Run migrations
bench --site YOUR_SITE migrate
```

### First-Time Setup
After installation, configure these settings:

1. **Attendance Policy Settings** (created automatically as Single DocType)
   - Navigate to: Workspace → Attendance Policy → Attendance Policy Settings
   - Set Company
   - Configure timings (defaults: 09:00 cutoff, Grade 1 ends 10:00, Grade 2 ends 11:00, full-day at 13:30)
   - Set deduction fractions (defaults: 1/6, 1/3, 1/2, 1 full day)
   - Set report recipients (comma/newline separated emails)
   - Link Casual Leave Type and Annual Leave Type
   - Enable "Deduct from leave balance first" (recommended)
   - Configure salary component (default: "Late Arrival Deduction")

2. **Holiday List** (built-in ERPNext)
   - HR → Holiday List → Create new
   - Add Sundays (weekly off) + gazetted holidays
   - Assign to Company or Employees

3. **Shift Types** (built-in HRMS)
   - HR → Shift Type → Create shifts:
     - **Mon-Thu & Sat**: 8 working hours, 1h break, flexible arrival 08:30-09:00
     - **Friday**: 7 working hours, 2h break
   - Assign shifts to employees (Shift Assignment)

4. **Leave Types** (built-in HRMS)
   - HR → Leave Type → Configure:
     - **Casual/Sick Leave**: 
       - Max continuous days = 3
       - Allow encashment = Yes
       - Max encashment = 10
       - Include holidays = based on policy
     - **Annual Leave**:
       - Earned leave = Yes (after 12 months)
       - Include holidays/Sundays = Yes

5. **Leave Policy & Allocation** (built-in HRMS)
   - Create Leave Policy with 15 Casual + 15 Annual days
   - Create Leave Allocations for employees

6. **Salary Component** (auto-created on install)
   - Payroll → Salary Component → "Late Arrival Deduction" (Type: Deduction)
   - Verify it exists; created automatically by `after_install` hook

## Usage

### Daily Operations
The app runs automatically via scheduled jobs:
- **9:00 PM daily**: Processes the day's check-ins, grades late arrivals, sends email report
- **11:30 PM daily**: Runs month-end processing (only acts on last day of month)

#### Manual Daily Run (Testing/Reprocessing)
```bash
# Process today
bench --site YOUR_SITE execute attendance_policy.tasks.daily_job

# Process specific date (idempotent, won't create duplicates)
bench --site YOUR_SITE execute attendance_policy.tasks.daily_job --kwargs "{'date':'2026-10-15'}"
```

#### Manual Month-End Run
```bash
# Dry run (preview only, no commits)
bench --site YOUR_SITE execute attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end --kwargs "{'period_end':'2026-10-31','dry_run':True}"

# Actual processing
bench --site YOUR_SITE execute attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end --kwargs "{'period_end':'2026-10-31','dry_run':False}"
```

Or use the desk UI:
1. Open browser console on Attendance Policy Settings page
2. Run:
```javascript
frappe.call({
    method: 'attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end',
    args: {period_end: '2026-10-31', dry_run: true},
    callback: (r) => console.log(r.message)
});
```

### Reports & Analytics
- **Daily Attendance Summary**: View check-in/out and late grades for any date
- **Habitual Late Comers**: Analyze late patterns with configurable threshold
- **Late Arrivals Dashboard**: 
  - Late count by grade (bar chart)
  - Top 10 late employees (bar chart)
  - Daily trend (line chart)

Access via: Workspace → Attendance Policy → Reports

### Month-End Flow
1. **Throughout month**: Daily job creates Late Arrival Logs (status: Pending)
2. **Last day of month** (automated at 11:30 PM or manual trigger):
   - Sum pending logs per employee
   - Deduct from casual leave balance first (creates Leave Ledger Entry)
   - Remainder deducted as Additional Salary (Deduction)
   - Creates Late Deduction Entry linking all entries
   - Marks logs as Processed
3. **Salary Slip generation**: Additional Salary automatically reduces the salary

## Built-in vs Custom

### Built-in ERPNext/HRMS Features Used
✅ **Holiday List**: Company holidays, weekly offs  
✅ **Shift Types**: Working hours, flexible timings, grace periods  
✅ **Leave Types**: Casual/Annual leave configuration, encashment, max consecutive days  
✅ **Leave Policy & Allocation**: Annual entitlement, proration  
✅ **Leave Application**: Approval workflow, balance checking  
✅ **Salary Structure Assignment**: Base salary for deduction calculation  
✅ **Additional Salary**: Month-end deductions (auto-picked by Salary Slip)  
✅ **Leave Ledger Entry**: Leave balance adjustments  
✅ **Employee Checkin**: Attendance tracking (first IN = arrival, last OUT = exit)

### Custom App Components
🔧 **DocTypes**:
- Attendance Policy Settings (Single)
- Late Arrival Log
- Late Deduction Entry

🔧 **Scheduled Jobs**:
- Daily attendance grading & email (9 PM)
- Month-end deduction processing (11:30 PM, last day only)

🔧 **Leave Validations** (doc_events on Leave Application):
- Casual leave: max consecutive days check, holiday adjacency warning
- Annual leave: 12-month eligibility, advance application, max 2 parts/year

🔧 **Reports**:
- Daily Attendance Summary
- Habitual Late Comers

🔧 **Dashboard & Workspace**:
- Late Arrivals dashboard (3 charts)
- Attendance Policy workspace

## Testing

### Run Unit Tests
```bash
# Run all tests
bench --site YOUR_SITE run-tests --app attendance_policy

# Run specific test
bench --site YOUR_SITE run-tests --app attendance_policy --module attendance_policy.tests.test_late_grading
```

### Manual Testing Checklist

#### 1. Setup Test Data
```python
# In bench console: bench --site YOUR_SITE console

# Create test employees
emp1 = frappe.get_doc({
    "doctype": "Employee",
    "first_name": "Test",
    "last_name": "Employee1",
    "company": "Your Company",
    "date_of_joining": "2025-01-01",
    "status": "Active"
}).insert()

# Create check-ins for different grades
from datetime import datetime
frappe.get_doc({
    "doctype": "Employee Checkin",
    "employee": emp1.name,
    "time": datetime(2026, 10, 28, 9, 30, 0)  # Grade 1
}).insert()

frappe.get_doc({
    "doctype": "Employee Checkin",
    "employee": emp1.name,
    "time": datetime(2026, 10, 28, 17, 30, 0)  # Exit
}).insert()
```

#### 2. Test Daily Job
```bash
bench --site YOUR_SITE execute attendance_policy.tasks.daily_job --kwargs "{'date':'2026-10-28'}"
```
Verify:
- Late Arrival Log created with correct grade
- Email sent to configured recipients
- No duplicate logs on re-run

#### 3. Test Leave Validations
- Create Leave Application (Casual): Try > 3 days → should block
- Create Leave Application (Casual): Adjacent to Sunday without reason → should warn
- Create Leave Application (Annual): Employee < 12 months → should block
- Create Leave Application (Annual): Apply for past date (non-HR Manager) → should block

#### 4. Test Month-End
```bash
# Dry run first
bench --site YOUR_SITE execute attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end --kwargs "{'period_end':'2026-10-31','dry_run':True}"

# Check casual leave balance
bench --site YOUR_SITE console
>>> from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
>>> get_leave_balance_on("EMP-001", "Casual Leave", "2026-10-31")

# Actual processing
bench --site YOUR_SITE execute attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end --kwargs "{'period_end':'2026-10-31','dry_run':False}"
```
Verify:
- Late Deduction Entry created
- Leave Ledger Entry created (if balance available)
- Additional Salary created for remainder
- Logs marked as Processed
- Re-run is idempotent (no double deduction)

#### 5. Test Salary Slip
```bash
# Generate salary slip for month
# Payroll → Salary Slip → Create new
# Select employee and month
# Verify Additional Salary (Late Arrival Deduction) appears in deductions
```

## File Structure
```
attendance_policy/
├── attendance_policy/
│   ├── attendance_policy/
│   │   ├── doctype/
│   │   │   ├── attendance_policy_settings/
│   │   │   ├── late_arrival_log/
│   │   │   └── late_deduction_entry/
│   │   ├── report/
│   │   │   ├── daily_attendance_summary/
│   │   │   └── habitual_late_comers/
│   │   └── workspace/
│   │       └── attendance_policy/
│   ├── tests/
│   │   └── test_late_grading.py
│   ├── hooks.py          # App registration, scheduler, doc_events
│   ├── install.py        # After-install setup
│   ├── leave_rules.py    # Leave Application validations
│   ├── tasks.py          # Daily and month-end jobs
│   └── modules.txt
├── pyproject.toml
└── README.md
```

## Configuration Options

### Attendance Policy Settings Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| company | Link | - | Company for this policy |
| arrival_cutoff | Time | 09:00:00 | On-time threshold |
| grade1_end | Time | 10:00:00 | Grade 1 upper bound |
| grade2_end | Time | 11:00:00 | Grade 2 upper bound |
| second_half_cutoff | Time | 13:30:00 | Full-day leave threshold |
| grade1_deduction | Float | 0.166667 | 1/6 day |
| grade2_deduction | Float | 0.333333 | 1/3 day |
| grade3_deduction | Float | 0.5 | 1/2 day |
| full_day_deduction | Float | 1.0 | Full day |
| habitual_threshold | Int | 3 | Min late count for "habitual" |
| report_recipients | Small Text | - | Email recipients (comma/newline) |
| casual_leave_type | Link | - | Leave Type for casual leave |
| annual_leave_type | Link | - | Leave Type for annual leave |
| max_consecutive_casual | Int | 3 | Max consecutive casual days |
| deduct_from_leave_first | Check | 1 | Deduct from leave before salary |
| salary_component | Link | Late Arrival Deduction | Deduction component |
| salary_days_divisor | Int | 30 | Days per month for calculation |
| create_journal_entry | Check | 0 | Also create JE (usually OFF) |
| je_debit_account | Link | - | JE debit account |
| je_credit_account | Link | - | JE credit account |

## Known Limitations

1. **Holiday adjacency counting**: Currently validates that casual leave adjacent to holidays requires justification, but does not automatically add holiday days to the leave count. This requires manual verification by approver.

2. **Shift-specific rules**: The app uses fixed time boundaries for all employees. If you need different times per shift, you'll need to customize `tasks.get_grade()` to check the employee's shift.

3. **Biometric integration**: Assumes Employee Checkin records are already created by your biometric/attendance device integration. This app does not directly read from devices.

4. **Multi-company**: Settings are per-company, but scheduled jobs process all active employees. For true multi-company isolation with different rules, you may need separate sites.

5. **Timezone**: Assumes server timezone matches your office timezone. If not, adjust the datetime filters in `tasks.daily_job()`.

6. **WCAG compliance**: Forms and reports use standard Frappe UI components, but full accessibility compliance requires manual testing with assistive technologies.

## Troubleshooting

### Daily job not running
- Check scheduler status: `bench --site YOUR_SITE doctor`
- Check scheduler is enabled in site_config.json: `disable_scheduler` should not be 1
- Check logs: `tail -f logs/error.log`

### Email not sending
- Verify Email Account configured: Setup → Email Account
- Check report_recipients in Attendance Policy Settings
- Check outgoing email queue: Setup → Email Queue

### Month-end not deducting
- Verify Salary Structure Assignment exists for employee
- Check casual leave balance: `get_leave_balance_on()`
- Check Late Arrival Logs status (should be Pending)
- Review error logs: Late deduction errors are logged with employee name

### Leave validation not working
- Check doc_events hook is registered in hooks.py
- Run `bench migrate` to reload hooks
- Check Leave Type names match Settings exactly

## Support & Contributing

For issues, feature requests, or contributions, please open an issue/PR on the GitHub repository.

## License

MIT

## Credits

Built for ERPNext v16 + HRMS v16 (Frappe Framework v16)
