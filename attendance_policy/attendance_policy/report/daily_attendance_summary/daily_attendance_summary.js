frappe.query_reports["Daily Attendance Summary"] = {
	filters: [
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (column.fieldname === "status") {
			if (data.status === "On Time") {
				return `<span class="indicator-pill green" style="font-weight: 600;">${__("On Time")}</span>`;
			} else if (data.status === "Late") {
				return `<span class="indicator-pill red" style="font-weight: 600;">${__("Late")}</span>`;
			}
		}

		if (column.fieldname === "late_grade" && data.late_grade) {
			let color_map = {
				"Grade 1": "background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a;",
				"Grade 2": "background-color: #ffedd5; color: #9a3412; border: 1px solid #fed7aa;",
				"Grade 3": "background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca;",
			};
			let style = color_map[data.late_grade] || "background-color: #f3f4f6; color: #374151;";
			return `<span style="padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; ${style}">${data.late_grade}</span>`;
		}

		if (column.fieldname === "check_in" && value) {
			return `<span style="font-weight: 600; color: #1e293b;">${value}</span>`;
		}

		return value;
	},
};
