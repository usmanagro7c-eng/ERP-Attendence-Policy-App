// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.query_reports["Late Comers by Grade"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (column.fieldname === "total" && data.total > 0) {
			return `<span style="font-weight: 700; color: #b91c1c; font-size: 13px;">${data.total}</span>`;
		}
		if (column.fieldname === "g1" && data.g1 > 0) {
			return `<span style="color: #b45309; font-weight: 600; background: #fef3c7; padding: 2px 8px; border-radius: 10px;">${data.g1}</span>`;
		}
		if (column.fieldname === "g2" && data.g2 > 0) {
			return `<span style="color: #c2410c; font-weight: 600; background: #ffedd5; padding: 2px 8px; border-radius: 10px;">${data.g2}</span>`;
		}
		if (column.fieldname === "g3" && data.g3 > 0) {
			return `<span style="color: #b91c1c; font-weight: 700; background: #fee2e2; padding: 2px 8px; border-radius: 10px;">${data.g3}</span>`;
		}
		if (column.fieldname === "dates" && data.dates) {
			return `<span class="text-muted" style="font-size: 11px;">${data.dates}</span>`;
		}
		return value;
	},
};
