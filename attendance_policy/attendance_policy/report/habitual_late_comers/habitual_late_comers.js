frappe.query_reports["Habitual Late Comers"] = {
	filters: [
		{ fieldname: "from_date", label: __("From Date"), fieldtype: "Date", default: frappe.datetime.month_start(), reqd: 1 },
		{ fieldname: "to_date", label: __("To Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
		{ fieldname: "min_count", label: __("Min Late Count"), fieldtype: "Int" },
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (column.fieldname === "total" && data.total >= 3) {
			return `<span class="indicator-pill red" style="font-weight: 700;">${data.total} Late</span>`;
		}
		if (column.fieldname === "days" && data.days > 0) {
			return `<span style="font-weight: 700; color: #dc2626;">-${parseFloat(data.days).toFixed(2)}d</span>`;
		}
		if (column.fieldname === "g1" && data.g1 > 0) {
			return `<span style="color: #b45309; font-weight: 600;">${data.g1}</span>`;
		}
		if (column.fieldname === "g2" && data.g2 > 0) {
			return `<span style="color: #c2410c; font-weight: 600;">${data.g2}</span>`;
		}
		if (column.fieldname === "g3" && data.g3 > 0) {
			return `<span style="color: #b91c1c; font-weight: 700;">${data.g3}</span>`;
		}
		return value;
	},
};
