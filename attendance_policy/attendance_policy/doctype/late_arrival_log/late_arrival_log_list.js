frappe.listview_settings["Late Arrival Log"] = {
	add_fields: ["grade", "status", "deduction_days", "arrival_time", "employee_name", "attendance_date"],
	get_indicator: function (doc) {
		if (doc.status === "Processed") {
			return [__("Processed"), "green", "status,=,Processed"];
		}
		if (doc.grade === "Grade 3") {
			return [__("Grade 3"), "red", "grade,=,Grade 3|status,=,Pending"];
		} else if (doc.grade === "Grade 2") {
			return [__("Grade 2"), "orange", "grade,=,Grade 2|status,=,Pending"];
		} else if (doc.grade === "Grade 1") {
			return [__("Grade 1"), "yellow", "grade,=,Grade 1|status,=,Pending"];
		}
		return [__("Pending"), "orange", "status,=,Pending"];
	},
	formatters: {
		grade: function (val) {
			if (!val) return "";
			let color_map = {
				"Grade 1": "color: #b45309; background-color: #fef3c7; border: 1px solid #fde68a;",
				"Grade 2": "color: #c2410c; background-color: #ffedd5; border: 1px solid #fed7aa;",
				"Grade 3": "color: #b91c1c; background-color: #fee2e2; border: 1px solid #fecaca;",
			};
			let style = color_map[val] || "color: #374151; background-color: #f3f4f6;";
			return `<span style="padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block; ${style}">${frappe.utils.escape_html(val)}</span>`;
		},
		deduction_days: function (val) {
			if (val === undefined || val === null || val === "") return "";
			return `<span style="font-weight: 600; color: #dc2626;">-${parseFloat(val).toFixed(2)}d</span>`;
		},
		status: function (val) {
			if (val === "Processed") {
				return `<span class="indicator-pill green" style="font-weight: 600;">${__("Processed")}</span>`;
			}
			return `<span class="indicator-pill orange" style="font-weight: 600;">${__("Pending")}</span>`;
		},
	},
};
