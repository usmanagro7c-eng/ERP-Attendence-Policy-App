# Changelog

All notable changes to the `attendance_policy` Frappe custom app will be documented in this file.

## [v0.0.3] - 2026-10-30

### Added
- **Biometric Check-in Ingestion:** Added `include_skip_auto_attendance_checkins` in `Attendance Policy Settings` (default `1` / ON) to process `Employee Checkin` records created by biometric synchronization tools (such as `zkteco_sync`) that mark punches with `skip_auto_attendance=1`.
- **Company-Scoped Daily Processing:** Scoped absent detection and checkin evaluation to `s.company` when configured, aligning processing with the target company (e.g. `Usman`).
- **Integration Test:** Added `test_daily_job_with_skip_auto_attendance_biometric` verifying biometric check-in ingestion and toggle behavior.

---

## [v0.0.2] - 2026-10-29

### Added
- **Settings Validation:** Mandatory constraints on deduction fractions (0..1), ascending cutoffs, positive divisor, valid non-party Journal Entry accounts, and recipient emails.
- **Adjacent Holiday Leave Counting:** Added `count_adjacent_holidays` setting to count Sunday/holiday chains as leaves when Leave Application Reason is empty (creates and reconciles extra Leave Ledger Entries).
- **Casual Leave Encashment Cap:** Validates that total casual leave encashed does not exceed `max_encashable_days` (default 10) in a calendar year.
- **In-App HR Notifications:** Generates deduplicated `Notification Log` for HR Managers at the end of the daily job.
- **"Late Comers by Grade" Report & Stacked Chart:** New Script Report with stacked bar chart, Dashboard Chart, and Workspace Number Cards ("Late Today", "Late This Month", "Habitual Late-Comers").
- **Settings Month-End UI Actions:** Added "Month-End Dry Run" (preview modal) and "Run Month-End" buttons in `Attendance Policy Settings`.
- **Default Configuration Automation:** Added whitelisted method and Settings button "Create Default Configuration" to idempotently provision Shifts, Leave Types, and Holiday Lists.
- **Salary Slip Unprocessed Late Warning:** Displays warning on Salary Slip creation/validation if pending late logs exist in the slip's period.
- **Comprehensive Frappe Unit Tests:** Integrated `FrappeTestCase` automated test suite runnable via `bench run-tests`.

### Fixed
- **Stale Pending Logs:** Month-end processing now picks up all unhandled Pending logs (`attendance_date <= period_end`).
- **Check-in Direction & Timing Robustness:** Handles `IN`/`OUT` and `skip_auto_attendance`; skips pre-hire and post-relieving employees; supports morning half-day leave skipping.
- **Check-in Modification Sync:** Updates exit/arrival on existing Pending Late Arrival Logs when check-ins are modified or added retroactively.

---

## [v0.0.1] - 2026-10-28

### Added
- Core late arrival grading across 4 slabs (Grade 1: 1/6 day, Grade 2: 1/3 day, Grade 3: 1/2 day, Second Half: 1.0 day).
- Scheduled daily attendance job (`daily_job`) with HTML email summary.
- Scheduled month-end job (`month_end_job`) with casual leave absorption and Additional Salary posting.
- Basic leave validations (max 3 consecutive casual days, 12-month annual leave service requirement, prior approval, max 2 parts per year).
- Habitual Late Comers Report and Late Arrivals Dashboard.
