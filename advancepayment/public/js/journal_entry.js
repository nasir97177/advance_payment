// Copyright (c) 2019, Ridhosribumi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.ui.form.on("Journal Entry", {
  refresh: function(frm){
    if(frm.doc.docstatus == 1) {
      frm.add_custom_button(__('Reversing Entry'), frm.events.make_reversing_entry, __("Make"));
      frm.page.set_inner_btn_group_as_primary(__("Make"));
    }
  },
  make_reversing_entry: function(frm){
    frappe.model.open_mapped_doc({
  		method: "advancepayment.reference.make_reverse_journal",
  		frm: cur_frm
  	})
  },
  get_amount: function(frm){
    if(frm.doc.temp_jv){
      var str = frm.doc.temp_jv;
      var res = str.split("||");
      frm.set_value("delivery_note", res[0]);
      if(res[1] == "1"){
        frm.set_value("reversing_entry", "1");
      }
      frm.set_value("temp_si", res[2]);
    }
		frm.clear_table("accounts");
    frm.refresh_fields();
    if(!frm.doc.reversing_entry){
      return frappe.call({
  			method: 'advancepayment.reference.get_amount_dn',
  			args: {
  				dn: frm.doc.delivery_note,
          si: frm.doc.temp_si
  			},
  			callback: function(r, rt) {
  				if(r.message) {
  					$.each(r.message, function(i, d) {
  						var c = frm.add_child("accounts");
  						c.debit_in_account_currency = d.debit;
  						c.credit_in_account_currency = d.credit;
  					})
  					frm.refresh_fields();
  				}
  			}
  		})
    }else{
      return frappe.call({
  			method: 'advancepayment.reference.make_rjv',
  			args: {
  				dn: frm.doc.delivery_note,
          si: frm.doc.temp_si
  			},
  			callback: function(r, rt) {
  				if(r.message) {
  					$.each(r.message, function(i, d) {
  						var c = frm.add_child("accounts");
  						c.debit_in_account_currency = d.debit;
  						c.credit_in_account_currency = d.credit;
  					})
  					frm.refresh_fields();
  				}
  			}
  		})
    }
	},
	get_amount_si: function(frm){
		frm.clear_table("accounts");
		if(!frm.doc.rss_sales_invoice) return;
		return frappe.call({
			method: 'advancepayment.reference.get_amount_si',
			args: {
				si: frm.doc.rss_sales_invoice
			},
			callback: function(r, rt) {
				if(r.message) {
					$.each(r.message, function(i, d) {
						var c = frm.add_child("accounts");
						c.debit_in_account_currency = d.debit;
						c.credit_in_account_currency = d.credit;
					})
					frm.refresh_fields();
				}
			}
		})
	},
})
