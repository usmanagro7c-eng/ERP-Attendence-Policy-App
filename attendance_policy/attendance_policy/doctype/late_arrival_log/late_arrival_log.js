frappe.ui.form.on("Late Arrival Log", {
	refresh: function (frm) {
		render_summary_banner(frm);

		if (frm.doc.deduction_entry) {
			frm.add_custom_button(__("View Deduction Entry"), function () {
				frappe.set_route("Form", "Late Deduction Entry", frm.doc.deduction_entry);
			}, __("Actions"));
		}
	},
});

function render_summary_banner(frm) {
	if (!frm.doc.grade) return;

	let grade_colors = {
		"Grade 1": { bg: "#fef3c7", border: "#fde68a", text: "#92400e", badge_bg: "#f59e0b" },
		"Grade 2": { bg: "#ffedd5", border: "#fed7aa", text: "#9a3412", badge_bg: "#f97316" },
		"Grade 3": { bg: "#fee2e2", border: "#fecaca", text: "#991b1b", badge_bg: "#ef4444" },
	};
	let conf = grade_colors[frm.doc.grade] || { bg: "#f3f4f6", border: "#e5e7eb", text: "#374151", badge_bg: "#6b7280" };
	let status_badge = frm.doc.status === "Processed"
		? '<span class="badge" style="background-color: #10b981; color: white; padding: 5px 12px; border-radius: 12px; font-weight: 600; font-size: 12px;">✓ Processed</span>'
		: '<span class="badge" style="background-color: #f59e0b; color: white; padding: 5px 12px; border-radius: 12px; font-weight: 600; font-size: 12px;">⏳ Pending Deduction</span>';

	let arr_str = frm.doc.arrival_time ? frm.doc.arrival_time.substring(0, 5) : "--:--";
	let exit_str = frm.doc.exit_time ? frm.doc.exit_time.substring(0, 5) : "--:--";
	let date_str = frm.doc.attendance_date ? frappe.datetime.str_to_user(frm.doc.attendance_date) : "";

	let banner = `
		<div style="background: ${conf.bg}; border: 1px solid ${conf.border}; border-radius: 8px; padding: 12px 16px; margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
			<div style="display: flex; align-items: center; gap: 14px;">
				<span style="background: ${conf.badge_bg}; color: white; padding: 6px 14px; border-radius: 14px; font-weight: 700; font-size: 14px; letter-spacing: 0.5px;">
					${frm.doc.grade}
				</span>
				<div>
					<div style="font-weight: 600; font-size: 15px; color: ${conf.text};">
						${frm.doc.employee_name || frm.doc.employee} &mdash; ${date_str}
					</div>
					<div style="font-size: 12px; color: #4b5563; margin-top: 2px;">
						Check-in: <b>${arr_str}</b> &bull; Check-out: <b>${exit_str}</b> &bull; Penalty: <b style="color: #dc2626;">-${parseFloat(frm.doc.deduction_days || 0).toFixed(4)} days</b>
					</div>
				</div>
			</div>
			<div>
				${status_badge}
			</div>
		</div>
	`;
	frm.dashboard.clear_headline();
	frm.dashboard.set_headline(banner);
}
