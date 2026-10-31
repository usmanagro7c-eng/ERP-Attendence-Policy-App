// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance Policy Settings", {
	refresh: function (frm) {
		render_settings_dashboard(frm);

		if (frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager")) {
			frm.add_custom_button(__("Sync Machine & Grade Today"), function () {
				frappe.call({
					method: "attendance_policy.tasks.sync_biometric_and_grade_today",
					freeze: true,
					freeze_message: __("Syncing punches from biometric device and grading today..."),
					callback: function (r) {
						if (r.message) {
							frappe.msgprint({
								title: __("Sync & Grading Completed"),
								message: r.message,
								indicator: "green",
							});
						}
						frm.reload_doc();
					},
				});
			}, __("Actions"));

			frm.add_custom_button(__("Month-End Dry Run"), function () {
				show_month_end_dialog(frm, true);
			}, __("Actions"));

			frm.add_custom_button(__("Run Month-End"), function () {
				show_month_end_dialog(frm, false);
			}, __("Actions"));

			frm.add_custom_button(__("Create Default Configuration"), function () {
				frappe.confirm(
					__("This will provision standard Shifts, Leave Types, and Holiday List if they do not already exist. Proceed?"),
					function () {
						frappe.call({
							method: "attendance_policy.install.create_default_configuration",
							freeze: true,
							freeze_message: __("Provisioning default configuration..."),
							callback: function (r) {
								if (r.message) {
									let list_items = r.message.map((m) => `<li>${frappe.utils.escape_html(m)}</li>`).join("");
									frappe.msgprint({
										title: __("Configuration Result"),
										message: `<ul>${list_items}</ul>`,
										indicator: "green",
									});
								}
							},
						});
					}
				);
			}, __("Actions"));

			// Quick Links dropdown
			frm.add_custom_button(__("Late Arrival Logs"), function () {
				frappe.set_route("List", "Late Arrival Log");
			}, __("Quick Links"));

			frm.add_custom_button(__("Late Deduction Entries"), function () {
				frappe.set_route("List", "Late Deduction Entry");
			}, __("Quick Links"));

			frm.add_custom_button(__("Daily Attendance Report"), function () {
				frappe.set_route("query-report", "Daily Attendance Summary");
			}, __("Quick Links"));

			frm.add_custom_button(__("Late Comers by Grade"), function () {
				frappe.set_route("query-report", "Late Comers by Grade");
			}, __("Quick Links"));
		}
	},
});

function render_settings_dashboard(frm) {
	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Late Arrival Log",
			filters: { status: "Pending" },
		},
		callback: function (r1) {
			let pending_count = r1.message || 0;
			let exempt_count = (frm.doc.exempt_employees || []).length;
			let company = frm.doc.company || __("All Companies");

			let banner_html = `
				<div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
					<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
						<div>
							<div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600;">Attendance Policy Control Center</div>
							<div style="font-size: 20px; font-weight: 700; margin-top: 2px;">Company: ${frappe.utils.escape_html(company)}</div>
							<div style="font-size: 13px; color: #cbd5e1; margin-top: 4px;">
								Standard Arrival: <b>${frm.doc.arrival_cutoff || "09:00:00"}</b> &bull; Half-Day Cutoff: <b>${frm.doc.second_half_cutoff || "13:30:00"}</b>
							</div>
						</div>
						<div style="display: flex; gap: 12px; flex-wrap: wrap;">
							<div style="background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 6px; padding: 8px 16px; text-align: center; min-width: 120px;">
								<div style="font-size: 11px; text-transform: uppercase; color: #fbbf24; font-weight: 600;">Pending Late Logs</div>
								<div style="font-size: 22px; font-weight: 700; color: #fef08a;">${pending_count}</div>
							</div>
							<div style="background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 6px; padding: 8px 16px; text-align: center; min-width: 120px;">
								<div style="font-size: 11px; text-transform: uppercase; color: #a7f3d0; font-weight: 600;">Exempt Staff</div>
								<div style="font-size: 22px; font-weight: 700; color: #6ee7b7;">${exempt_count}</div>
							</div>
						</div>
					</div>
				</div>
			`;
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(banner_html);
		},
	});
}

function show_month_end_dialog(frm, is_dry_run) {
	let title = is_dry_run ? __("Month-End Dry Run Preview") : __("Run Month-End Processing");
	let action_label = is_dry_run ? __("Calculate Dry Run") : __("Post Deductions");

	let d = new frappe.ui.Dialog({
		title: title,
		fields: [
			{
				label: __("Period End Date"),
				fieldname: "period_end",
				fieldtype: "Date",
				reqd: 1,
				default: frappe.datetime.month_end(),
				description: __("Select the period end date to calculate or post deductions."),
			},
		],
		primary_action_label: action_label,
		primary_action: function (values) {
			if (!is_dry_run) {
				frappe.confirm(
					__("Are you sure you want to process and post deductions for period ending {0}? This will commit Leave Ledger Entries and Additional Salary deductions.", [values.period_end]),
					function () {
						d.hide();
						execute_month_end_call(values.period_end, 0);
					}
				);
			} else {
				d.hide();
				execute_month_end_call(values.period_end, 1);
			}
		},
	});
	d.show();
}

function execute_month_end_call(period_end, dry_run) {
	frappe.call({
		method: "attendance_policy.attendance_policy.doctype.attendance_policy_settings.attendance_policy_settings.process_month_end",
		args: {
			period_end: period_end,
			dry_run: dry_run,
		},
		freeze: true,
		freeze_message: dry_run ? __("Calculating month-end preview...") : __("Processing deductions..."),
		callback: function (r) {
			if (!r.message) return;
			let data = r.message;

			if (dry_run) {
				render_dry_run_modal(data, period_end);
			} else {
				frappe.msgprint({
					title: __("Month-End Completed"),
					message: __("Processed {0} employee(s) for period ending {1}.", [data.employees_processed, data.period_end]),
					indicator: "green",
				});
				cur_frm.reload_doc();
			}
		},
	});
}

function render_dry_run_modal(data, period_end) {
	let details = data.details || [];
	let total_late = 0;
	let total_leave = 0;
	let total_salary_days = 0;
	let total_salary_amt = 0;

	details.forEach((row) => {
		total_late += parseFloat(row.late_days || 0);
		total_leave += parseFloat(row.from_leave || 0);
		total_salary_days += parseFloat(row.from_salary || 0);
		total_salary_amt += parseFloat(row.salary_amount || 0);
	});

	let rows_html = "";
	if (details.length === 0) {
		rows_html = `<tr><td colspan="7" class="text-muted text-center" style="padding: 24px; font-size: 13px;">${__("No pending late arrival logs to process for this period. Everything is up to date!")}</td></tr>`;
	} else {
		details.forEach((row) => {
			rows_html += `
				<tr style="transition: background-color 0.15s ease;">
					<td style="padding: 8px 12px; font-weight: 600;">${frappe.utils.escape_html(row.employee)}</td>
					<td style="padding: 8px 12px;">${frappe.utils.escape_html(row.employee_name)}</td>
					<td style="padding: 8px 12px; text-align: right; font-weight: 600; color: #2563eb;">${parseFloat(row.late_days || 0).toFixed(2)}d</td>
					<td style="padding: 8px 12px; text-align: right; color: #0d9488;">${parseFloat(row.from_leave || 0).toFixed(2)}d</td>
					<td style="padding: 8px 12px; text-align: right; color: #ea580c;">${parseFloat(row.from_salary || 0).toFixed(2)}d</td>
					<td style="padding: 8px 12px; text-align: right; font-weight: 700; color: #dc2626;">${format_currency(row.salary_amount)}</td>
					<td style="padding: 8px 12px; text-align: center;"><span class="badge" style="background: #e2e8f0; color: #334155; font-size: 11px;">${row.logs}</span></td>
				</tr>
			`;
		});
	}

	let html = `
		<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 16px;">
			<div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 10px; text-align: center;">
				<div style="font-size: 11px; text-transform: uppercase; color: #1e40af; font-weight: 600;">Employees</div>
				<div style="font-size: 18px; font-weight: 700; color: #1d4ed8;">${data.employees_processed || 0}</div>
			</div>
			<div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 10px; text-align: center;">
				<div style="font-size: 11px; text-transform: uppercase; color: #166534; font-weight: 600;">Late Days</div>
				<div style="font-size: 18px; font-weight: 700; color: #15803d;">${total_late.toFixed(2)}d</div>
			</div>
			<div style="background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 6px; padding: 10px; text-align: center;">
				<div style="font-size: 11px; text-transform: uppercase; color: #115e59; font-weight: 600;">From Leave</div>
				<div style="font-size: 18px; font-weight: 700; color: #0f766e;">${total_leave.toFixed(2)}d</div>
			</div>
			<div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; padding: 10px; text-align: center;">
				<div style="font-size: 11px; text-transform: uppercase; color: #9a3412; font-weight: 600;">From Salary</div>
				<div style="font-size: 18px; font-weight: 700; color: #c2410c;">${total_salary_days.toFixed(2)}d</div>
			</div>
			<div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 10px; text-align: center;">
				<div style="font-size: 11px; text-transform: uppercase; color: #991b1b; font-weight: 600;">Salary Amount</div>
				<div style="font-size: 18px; font-weight: 700; color: #b91c1c;">${format_currency(total_salary_amt)}</div>
			</div>
		</div>

		<div style="max-height: 340px; overflow-y: auto; border: 1px solid var(--border-color, #e5e7eb); border-radius: 6px;">
			<table class="table table-bordered table-hover" style="font-size: 12px; margin-bottom: 0;">
				<thead style="background: var(--bg-light-gray, #f8fafc); position: sticky; top: 0; z-index: 1;">
					<tr>
						<th>${__("Employee")}</th>
						<th>${__("Name")}</th>
						<th style="text-align: right;">${__("Late Days")}</th>
						<th style="text-align: right;">${__("From Leave")}</th>
						<th style="text-align: right;">${__("From Salary")}</th>
						<th style="text-align: right;">${__("Amount")}</th>
						<th style="text-align: center;">${__("Logs")}</th>
					</tr>
				</thead>
				<tbody>
					${rows_html}
				</tbody>
			</table>
		</div>
		<p class="text-muted small" style="margin-top: 10px; margin-bottom: 0;">
			<i class="fa fa-info-circle"></i> <i>Dry run preview only. No salary slips or leave ledgers were modified.</i>
		</p>
	`;

	let modal = new frappe.ui.Dialog({
		title: __("Month-End Dry Run Preview ({0})", [period_end]),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "preview_html",
				options: html,
			},
		],
		primary_action_label: details.length > 0 ? __("Post Deductions Now") : __("Close"),
		primary_action: function () {
			if (details.length > 0) {
				frappe.confirm(
					__("Are you sure you want to execute and commit these deductions for period ending {0}?", [period_end]),
					function () {
						modal.hide();
						execute_month_end_call(period_end, 0);
					}
				);
			} else {
				modal.hide();
			}
		},
		secondary_action_label: details.length > 0 ? __("Close") : null,
		secondary_action: function () {
			modal.hide();
		},
	});
	modal.show();
}
