frappe.ui.form.on("Late Deduction Entry", {
	refresh: function (frm) {
		render_kpi_dashboard(frm);

		if (frm.doc.additional_salary) {
			frm.add_custom_button(__("View Additional Salary"), function () {
				frappe.set_route("Form", "Additional Salary", frm.doc.additional_salary);
			}, __("Linked Records"));
		}
		if (frm.doc.leave_ledger_entry) {
			frm.add_custom_button(__("View Leave Ledger"), function () {
				frappe.set_route("Form", "Leave Ledger Entry", frm.doc.leave_ledger_entry);
			}, __("Linked Records"));
		}
		if (frm.doc.journal_entry) {
			frm.add_custom_button(__("View Journal Entry"), function () {
				frappe.set_route("Form", "Journal Entry", frm.doc.journal_entry);
			}, __("Linked Records"));
		}
	},
});

function render_kpi_dashboard(frm) {
	let late_days = parseFloat(frm.doc.late_days || 0).toFixed(2);
	let from_leave = parseFloat(frm.doc.from_leave || 0).toFixed(2);
	let from_salary = parseFloat(frm.doc.from_salary || 0).toFixed(2);
	let salary_amt = format_currency(frm.doc.salary_amount || 0);

	let cards = `
		<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 15px;">
			<div style="background: var(--card-bg, #ffffff); border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
				<div style="font-size: 11px; text-transform: uppercase; font-weight: 600; color: var(--text-muted, #6b7280); letter-spacing: 0.5px;">Total Late Days</div>
				<div style="font-size: 22px; font-weight: 700; color: #2563eb; margin-top: 4px;">${late_days} <span style="font-size: 13px; font-weight: 400; color: #6b7280;">days</span></div>
			</div>
			<div style="background: var(--card-bg, #ffffff); border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
				<div style="font-size: 11px; text-transform: uppercase; font-weight: 600; color: var(--text-muted, #6b7280); letter-spacing: 0.5px;">Deducted From Leave</div>
				<div style="font-size: 22px; font-weight: 700; color: #0d9488; margin-top: 4px;">${from_leave} <span style="font-size: 13px; font-weight: 400; color: #6b7280;">days</span></div>
			</div>
			<div style="background: var(--card-bg, #ffffff); border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
				<div style="font-size: 11px; text-transform: uppercase; font-weight: 600; color: var(--text-muted, #6b7280); letter-spacing: 0.5px;">Deducted From Salary</div>
				<div style="font-size: 22px; font-weight: 700; color: #ea580c; margin-top: 4px;">${from_salary} <span style="font-size: 13px; font-weight: 400; color: #6b7280;">days</span></div>
			</div>
			<div style="background: var(--card-bg, #ffffff); border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
				<div style="font-size: 11px; text-transform: uppercase; font-weight: 600; color: var(--text-muted, #6b7280); letter-spacing: 0.5px;">Salary Deduction Cut</div>
				<div style="font-size: 22px; font-weight: 700; color: #dc2626; margin-top: 4px;">${salary_amt}</div>
			</div>
		</div>
	`;
	frm.dashboard.clear_headline();
	frm.dashboard.set_headline(cards);
}
