// Copyright (c) 2019, Ridhosribumi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.ui.form.on('Purchase Invoice', {
	refresh: function(frm){
		frm.events.set_total_purchase_receipt(frm);
	},
	onload: function(frm){
		frm.set_query("purchase_order", function (doc) {
			return {
				filters: {
					'docstatus': 1,
					'status': ["!=", "Completed"],
					'title': doc.supplier
				}
			}
		});
		frm.set_query("purchase_receipt", function (doc) {
			return {
				filters: {
					'docstatus': 1,
					'status': ["!=", "Completed"],
					'title': doc.supplier
				}
			}
		});
		frm.set_query('purchase_receipt', 'delivery', function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					'docstatus': 1,
					'status': ["!=", "Completed"],
					'title': doc.supplier
				}
			}
		});
		frm.set_query('purchase_invoice', 'related', function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					'docstatus': 1,
					'title': doc.supplier
				}
			}
		});
	},
 	validate: function(frm) {
		frm.events.set_total_purchase_receipt(frm);
		frm.events.set_total_related_invoice(frm);
		frm.events.validate_percentage(frm);
		frm.events.validate_get_items(frm);
		frm.events.validate_get_items2(frm);
		frm.events.validate_adjustment_tax(frm);
	},

	validate_get_items2: function(frm){
		if(frm.doc.type_of_invoice == "Termin Payment"){
			if(frm.doc.count_get_items2 == 0){
				msgprint("You have not clicked 'Get Items'");
				validated = false;
			}
		}
	},

  validate_percentage: function(frm){
    if(frm.doc.type_of_invoice == "Down Payment" || frm.doc.type_of_invoice == "Progress Payment" || frm.doc.type_of_invoice == "Payment"){
			if(flt(frm.doc.percentage_dp) >= 100 || flt(frm.doc.percentage_dp) <= 0){
				msgprint("Percentage should not be greater than 100 or less than 0");
				validated = false;
			}
		}
	},

	validate_get_items:function(frm){
		if(frm.doc.type_of_invoice == 'Down Payment' || frm.doc.type_of_invoice == 'Progress Payment'){
			if(frm.doc.get_items_count == 0){
				msgprint("You must press the Get Items button");
				validated = false;
			}
		}
	},

  get_items: function(frm){
    frm.set_value("get_items_count","1");
    frm.clear_table("items");
    if(frm.doc.type_of_invoice == "Down Payment"){
      var jenis = frm.doc.purchase_order
		}else if(frm.doc.type_of_invoice == "Progress Payment"){
      var jenis = frm.doc.purchase_receipt
    }
    return frappe.call({
      method : 'advancepayment.reference1.get_items_tampungan',
      args: {
        related_doc: jenis,
        tipe: frm.doc.type_of_invoice,
        percen: frm.doc.percentage_dp,
				company: frm.doc.company
      },
      callback: function(r, rt){
        if(r.message){
          $.each(r.message, function(i,d){
            var c = frm.add_child("items");
            c.item_code = d.item_code;
            c.item_name = d.item_name;
            c.description = d.description;
            c.qty = d.qty;
            c.uom = d.uom;
            c.rate = d.rate;
            c.amount = d.amount;
            c.expense_account = d.expense_account;
          })
          frm.refresh_fields();
        }
      }
    })
  },

  type_of_invoice: function(frm){
		if(frm.doc.type_of_invoice == 'Termin Payment'){
  		frm.set_value("count_get_items2","0");
			frm.clear_table("delivery");
			if(!frm.doc.purchase_order) return;
			return frappe.call({
					method : 'advancepayment.reference1.get_purchase_receipt',
					args: {
						purchase_order: frm.doc.purchase_order
					},
					callback: function(r, rt){
						if(r.message){
							$.each(r.message, function(i,d){
								var c = frm.add_child("delivery");
								c.purchase_receipt = d.purchase_receipt;
								c.posting_date = d.posting_date;
								c.total = d.total;
								c.net_total = d.net_total;
							})
							frm.refresh_fields();
							frm.events.set_total_purchase_receipt(frm);
						}
					}
			})
		}else if(frm.doc.type_of_invoice == 'Retention'){
 			frm.clear_table("related");
 			if(!frm.doc.purchase_order) return;
 			return frappe.call({
 					method : 'advancepayment.reference1.get_purchase_invoice',
 					args: {
 						purchase_order: frm.doc.purchase_order,
 						tipe: frm.doc.type_of_invoice
 					},
 					callback: function(r,rt){
 						if(r.message){
 							$.each(r.message,function(i,d){
 								var c = frm.add_child("related");
 								c.purchase_invoice = d.purchase_invoice;
 								c.posting_date = d.posting_date;
 								c.total = d.total;
 								c.net_total = d.net_total;
 							})
 							frm.refresh_fields();
 							frm.events.set_total_related_invoice(frm);
 							frm.events.buying_write_off(frm);
 						}
 					}
 			})
    }else if(frm.doc.type_of_invoice == "Non Project Payment"){
			frm.clear_table("related");
			return frappe.call({
				method: 'advancepayment.reference1.get_purchase_invoice2',
				args: {
					purchase_order: frm.doc.purchase_order || "none",
					delivery: frm.doc.purchase_receipt || "none",
					tipe: frm.doc.type_of_invoice,
					total: frm.doc.net_total
				},
				callback: function(r,rt){
					if(r.message){
						$.each(r.message,function(i,d){
							var c = frm.add_child("related");
							c.purchase_invoice = d.purchase_invoice;
							c.posting_date = d.posting_date;
							c.total = d.total;
							c.net_total = d.net_total;
						})
						frm.refresh_fields();
						frm.events.set_total_related_invoice(frm);
						frm.events.buying_write_off(frm);
					}
				}
			})
		}
  },
	purchase_order: function(frm){
		frm.events.type_of_invoice(frm);
	},
	buying_write_off: function(frm){
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Item Settings",
			},
			callback: function(data){
				frm.set_value("write_off_account",data.message.buying_write_off_account);
			}
		})
	},

	set_total_related_invoice: function(frm){
		var total_pi = 0.0;
		$.each(frm.doc.related,function(i,row){
			total_pi += flt(row.net_total);
		})
		frm.set_value("total_related_invoices",Math.abs(total_pi));
		frm.set_value("write_off_amount",Math.abs(total_pi));
	},

	set_total_purchase_receipt: function(frm){
		var total_pr = 0.0;
		$.each(frm.doc.delivery,function(i,row){
			total_pr += flt(row.total);
		})
		frm.set_value("total_purchase_receipt", Math.abs(total_pr));
	},

	percentage_dp: function(frm){
		frm.events.set_total_purchase_receipt(frm);
	},

	get_items2: function(frm){
		frm.events.set_total_purchase_receipt(frm);
		frm.set_value("count_get_items2","1");
		frm.clear_table("items");
		if(!frm.doc.purchase_order) return;
		return frappe.call({
			method : 'advancepayment.reference1.get_items_from_pelunasan',
			args: {
				purchase_order: frm.doc.purchase_order,
				total_delivery:frm.doc.total_purchase_receipt,
				percen: frm.doc.percentage_dp,
				company: frm.doc.company
			},
			callback: function(r,rt){
				if(r.message){
					$.each(r.message,function(i,d){
						var c = frm.add_child("items");
						c.item_code = d.item_code;
						c.item_name = d.item_name;
						c.description = d.description;
						c.qty = d.qty;
						c.uom = d.uom;
						c.rate = d.rate;
						c.amount = d.amount;
						c.expense_account = d.expense_account;
					})
					frm.refresh_fields();
				}
			}
		})
	},

	adjust_taxes_and_charges: function(frm, cdt, cdn) {
	  var tbl = frm.doc.taxes || [];
	  var i = tbl.length;
	  while (i--) {
		  if(frm.doc.taxes[i].charge_type != "Actual"){
			  var selisih = flt(frm.doc.net_total) - flt(frm.doc.write_off_amount);
			  var actual = (flt(frm.doc.taxes[i].tax_amount)/flt(frm.doc.net_total)) * selisih;
			  frm.doc.taxes[i].tax_amount = Math.abs(actual);
			  frm.doc.taxes[i].charge_type = "Actual";
			  frm.refresh_field("taxes");
		  }
	  }
	  frm.set_value("adjustment_count", "1");
	},

	validate_adjustment_tax: function(frm){
	  if(frm.doc.total_taxes_and_charges != 0){
		  if(frm.doc.type_of_invoice == "Retention" || frm.doc.type_of_invoice == "Non Project Payment"){
			  if(frm.doc.adjustment_count == 0){
				  msgprint("You have not clicked 'Adjust Taxes and Charges'");
				  validated = false;
			  }
		  }
	  }
	},
})
