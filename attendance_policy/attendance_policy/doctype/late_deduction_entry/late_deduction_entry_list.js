frappe.listview_settings["Late Deduction Entry"] = {
	add_fields: ["employee_name", "period_end", "late_days", "from_leave", "from_salary", "salary_amount", "additional_salary", "leave_ledger_entry"],
	get_indicator: function (doc) {
		if (doc.additional_salary || doc.leave_ledger_entry) {
			return [__("Posted"), "green", "docstatus,=,0"];
		}
		return [__("Processed"), "blue", "docstatus,=,0"];
	},
	formatters: {
		salary_amount: function (val) {
			if (val === undefined || val === null || val === "") return "";
			return `<span style="font-weight: 700; color: #dc2626;">${format_currency(val)}</span>`;
		},
		late_days: function (val) {
			if (val === undefined || val === null || val === "") return "";
			return `<span style="font-weight: 600; color: #b91c1c;">${parseFloat(val).toFixed(2)}d</span>`;
		},
		from_leave: function (val) {
			if (val === undefined || val === null || val === "") return "";
			return `<span style="color: #0d9488; font-weight: 500;">${parseFloat(val).toFixed(2)}d</span>`;
		},
		from_salary: function (val) {
			if (val === undefined || val === null || val === "") return "";
			return `<span style="color: #ea580c; font-weight: 500;">${parseFloat(val).toFixed(2)}d</span>`;
		},
	},
};
