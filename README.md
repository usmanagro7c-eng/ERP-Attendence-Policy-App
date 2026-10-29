# Attendance Policy

Complete Frappe custom app for ERPNext v16 + HRMS v16 that enforces company attendance and leave rules, automates late-arrival deductions, sends daily attendance emails, provides late-comer analytics, and posts month-end salary deductions.

---

## 🎯 Features

### 1. Daily Late Arrival Grading (Memo Section 3)
- **Arrival Cutoff (09:00 AM)**: Arrival $\le$ 09:00:00 $\rightarrow$ On-time (No deduction).
- **Grade 1 (09:00:01 to 10:00:00)**: $1/6$ day deduction (default `0.166667`).
- **Grade 2 (10:00:01 to 11:00:00)**: $1/3$ day deduction (default `0.333333`).
- **Grade 3 (11:00:01 to 13:30:00)**: $1/2$ day deduction (default `0.5`).
- **Second Half / Full Day (Arrival $\ge$ 13:30:00)**: $1$ full day deduction (default `1.0`).
- **Check-in Logic**: Uses first `IN` check-in for arrival time and last `OUT` check-in for exit time.
- **Half-Day Leave Tolerance**: Configurable toggle (`skip_morning_late_if_half_day_leave`) to skip morning late grading if an approved first-half leave exists.
- **Employment Boundaries**: Automatically ignores employees prior to their Date of Joining or after their Relieving Date.

### 2. Leave Policy Enforcements (Memo Section 4)
- **Casual / Sick Leave**:
  - Max consecutive days cap (default 3 days).
  - **Adjacent Holiday / Sunday Counting (Fix 1)**: If a Casual/Sick leave range is adjacent to a Sunday or gazetted holiday (before `from_date` or after `to_date`), and the employee leaves the `reason` field empty, the adjacent holiday days are counted as leave and deducted from the casual leave balance. If a justification/reason is provided, adjacent holidays are not deducted.
  - **Encashment Limit (Fix 2)**: Enforces a strict annual maximum encashment cap (default 10 days per calendar year / leave period).
- **Annual Leave**:
  - Minimum 12 months continuous service requirement.
  - Advance application required (only `HR Manager` can override retrospective applications).
  - Maximum 2 leave parts per calendar year.

### 3. Month-End Processing & Salary Deductions
- **Leave-First Splitting**: Deducts late days from available Casual Leave balance first (creating a `Leave Ledger Entry`). The remainder is converted into a monetary deduction via `Additional Salary` (type: Deduction).
- **Stale Pending Log Sweep**: Automatically catches and processes all pending logs where `date <= period_end`, ensuring logs from prior un-run months are never left behind.
- **Interactive UI**: "Month-End Dry Run" button in `Attendance Policy Settings` opens a modal table displaying per-employee deduction breakdowns before any records are committed.
- **Payroll Timing Warning**: Validates `Salary Slip` creation and warns HR with an orange indicator if unprocessed pending late logs exist in the salary slip date range.

### 4. Notifications & Analytics
- **Daily HTML Email Report**: Sent at 21:00 to configured recipients with check-in/out times, late grades, absent employees, and habitual late-comers.
- **Deduplicated In-App Notifications**: Alerts HR Managers with an in-app `Notification Log` summarizing late arrivals.
- **Script Reports**:
  - `Daily Attendance Summary`: Detailed daily attendance log.
  - `Habitual Late Comers`: Filtered by frequency threshold.
  - `Late Comers by Grade`: Multi-grade stacked bar chart and tabular breakdown by employee and department.
- **Dashboard & Workspace**: Dedicated `Attendance Policy` Workspace and Dashboard with real-time analytics.

---

## 🏛️ Architectural Design Choices

### Adjacent Holiday Leave Counting (`Leave Ledger Entry`)
When a Casual Leave application with adjacent holidays is submitted without justification:
1. The app creates a supplementary negative `Leave Ledger Entry` linked to the submitted `Leave Application` (`transaction_type="Leave Application"`, `transaction_name=doc.name`).
2. **Why this approach?**
   - In Frappe HRMS, `Leave Ledger Entry` is the source of truth for all leave balance calculations (`get_leave_balance_on`).
   - Standard HRMS lifecycle automatically deletes linked ledger entries when a `Leave Application` is cancelled (`on_cancel`).
   - This guarantees 100% transactional integrity: no orphan ledger entries on cancel/amend, accurate leave reports, and complete compatibility with ERPNext payroll.

### Recommended Payroll Order of Operations
To ensure accurate salary slip generation:
1. **Daily**: Automated job runs at 21:00 to grade daily check-ins.
2. **Month-End (Last Day of Month)**: 
   - Open **Attendance Policy Settings** $\rightarrow$ click **Actions $\rightarrow$ Month-End Dry Run** to preview deductions.
   - Click **Actions $\rightarrow$ Run Month-End** (or let the automated scheduler run at 23:30).
3. **Salary Slip Generation**: 
   - Generate Salary Slips for the month.
   - ERPNext will automatically pull in the `Additional Salary` late deductions created by the month-end job.
   - If HR attempts to create a Salary Slip while pending late logs remain, an orange banner will warn them.

---

## 🚫 Out of Scope

The following items are explicitly **out of scope** for this release:
- **Early Leaving Penalties**: The memo only penalizes late arrival. Early departures are recorded in the exit log but not penalized.
- **Lunch / Prayer Break Tracking**: Multiple daily check-ins for lunch/prayer breaks are not tracked or graded (standard biometrics only supply arrival and exit punches).

---

## ⚙️ Attendance Policy Settings Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `company` | Link (Company) | - | Target company |
| `arrival_cutoff` | Time | `09:00:00` | On-time arrival threshold |
| `grade1_end` | Time | `10:00:00` | Grade 1 upper bound |
| `grade2_end` | Time | `11:00:00` | Grade 2 upper bound |
| `second_half_cutoff` | Time | `13:30:00` | Full day deduction threshold |
| `grade1_deduction` | Float | `0.166667` | Deduction fraction for Grade 1 (1/6 day) |
| `grade2_deduction` | Float | `0.333333` | Deduction fraction for Grade 2 (1/3 day) |
| `grade3_deduction` | Float | `0.500000` | Deduction fraction for Grade 3 (1/2 day) |
| `full_day_deduction` | Float | `1.000000` | Deduction fraction for Full Day (1 day) |
| `casual_leave_type` | Link (Leave Type) | - | Link to Casual / Sick Leave Type |
| `annual_leave_type` | Link (Leave Type) | - | Link to Annual Leave Type |
| `count_adjacent_holidays` | Check | `1` | Count adjacent Sundays/holidays if reason is empty |
| `adjacent_holidays_in_3day_cap`| Check | `0` | Include counted holidays inside the 3-day consecutive limit |
| `max_consecutive_casual` | Int | `3` | Maximum consecutive casual leave days |
| `max_encashable_days` | Int | `10` | Maximum casual leave encashment days allowed per year |
| `skip_morning_late_if_half_day_leave` | Check | `1` | Do not mark morning late if approved first-half leave exists |
| `warn_salary_slip_pending_late` | Check | `1` | Show warning indicator on Salary Slip if pending late logs exist |
| `enable_hr_notification` | Check | `1` | Send in-app notification to HR Managers |
| `habitual_threshold` | Int | `3` | Monthly late threshold for habitual classification |
| `report_recipients` | Small Text | - | Comma or newline-separated recipient emails |
| `deduct_from_leave_first` | Check | `1` | Deduct from leave balance before salary |
| `salary_component` | Link (Salary Component) | `Late Arrival Deduction` | Salary component for cash deductions |
| `salary_days_divisor` | Int | `30` | Per-day salary calculation divisor |
| `create_journal_entry` | Check | `0` | Optionally generate direct journal entries |

---

## 🚀 Installation & Setup

### 1. Install App
```bash
cd /path/to/frappe-bench
bench get-app https://github.com/usmanagro7c-eng/ERP-Attendence-Policy-App.git
bench --site <YOUR_SITE> install-app attendance_policy
bench --site <YOUR_SITE> migrate
```

### 2. Auto-Provision Default Setup
You can automatically provision company shifts, leave types, and holiday lists:
1. Open **Attendance Policy Settings**.
2. Click **Actions $\rightarrow$ Setup Default Shifts & Policy**.
3. Select your Company and click **Create Configuration**.

---

## 🧪 Automated Testing

Run the full Frappe automated integration test suite:
```bash
bench --site <YOUR_SITE> run-tests --app attendance_policy
```

Expected result:
```
Ran 14 tests in ~7s
OK
Ran 5 tests in ~0.001s
OK
```

---

## 📄 License
MIT License.
