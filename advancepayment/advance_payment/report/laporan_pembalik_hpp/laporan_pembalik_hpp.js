// Copyright (c) 2019, Ridhosribumi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Laporan Pembalik HPP"] = {
	"filters": [
		{
			"fieldname":"month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": 'Januari\nFebruari\nMaret\nApril\nMei\nJuni\nJuli\nAgustus\nSeptember\nOktober\nNovember\nDesember',
			"reqd": 1
		},
		{
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd": 1
		},
	]
}
