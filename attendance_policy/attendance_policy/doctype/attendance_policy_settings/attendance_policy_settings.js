// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance Policy Settings", {
	refresh: function (frm) {
		if (frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager")) {
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
		}
	},
});

function show_month_end_dialog(frm, is_dry_run) {
	let title = is_dry_run ? __("Month-End Dry Run") : __("Run Month-End Processing");
	let action_label = is_dry_run ? __("Calculate Preview") : __("Post Deductions");

	let d = new frappe.ui.Dialog({
		title: title,
		fields: [
			{
				label: __("Period End Date"),
				fieldname: "period_end",
				fieldtype: "Date",
				reqd: 1,
				default: frappe.datetime.month_end(),
				description: __("Must be the last day of the target month."),
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
				render_dry_run_modal(data);
			} else {
				frappe.msgprint({
					title: __("Month-End Completed"),
					message: __("Processed {0} employee(s) for period ending {1}.", [data.employees_processed, data.period_end]),
					indicator: "green",
				});
			}
		},
	});
}

function render_dry_run_modal(data) {
	let rows_html = "";
	if (!data.details || data.details.length === 0) {
		rows_html = `<tr><td colspan="7" class="text-muted text-center" style="padding: 12px;">${__("No pending late arrival logs to process for this period.")}</td></tr>`;
	} else {
		data.details.forEach((row) => {
			rows_html += `
				<tr>
					<td style="padding: 6px 10px;">${frappe.utils.escape_html(row.employee)}</td>
					<td style="padding: 6px 10px;">${frappe.utils.escape_html(row.employee_name)}</td>
					<td style="padding: 6px 10px; text-align: right;">${row.late_days}</td>
					<td style="padding: 6px 10px; text-align: right;">${row.from_leave}</td>
					<td style="padding: 6px 10px; text-align: right;">${row.from_salary}</td>
					<td style="padding: 6px 10px; text-align: right;">${format_currency(row.salary_amount)}</td>
					<td style="padding: 6px 10px; text-align: center;">${row.logs}</td>
				</tr>
			`;
		});
	}

	let html = `
		<div style="margin-bottom: 10px;">
			<span class="indicator blue"><b>Period End:</b> ${frappe.utils.escape_html(data.period_end)}</span>
			<span class="indicator green" style="margin-left: 15px;"><b>Employees:</b> ${data.employees_processed}</span>
		</div>
		<table class="table table-bordered table-condensed" style="font-size: 12px; margin-top: 10px;">
			<thead style="background: var(--bg-light-gray);">
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
		<p class="text-muted small" style="margin-top: 8px;">
			<i>* Dry run preview only. No records were updated or inserted in the database.</i>
		</p>
	`;

	let modal = new frappe.ui.Dialog({
		title: __("Month-End Dry Run Preview"),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "preview_html",
				options: html,
			},
		],
		primary_action_label: __("Close"),
		primary_action: function () {
			modal.hide();
		},
	});
	modal.show();
}
