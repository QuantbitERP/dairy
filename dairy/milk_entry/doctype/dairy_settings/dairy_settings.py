# -*- coding: utf-8 -*-
# Copyright (c) 2019, Dexciss Technology by Sid and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date
from datetime import date, timedelta,datetime
from frappe.utils import (flt, getdate, get_url, now,
                          nowtime, get_time, today, get_datetime, add_days, datetime)

class DairySettings(Document):
	@frappe.whitelist()
	def custom_po(self):
		p_inv = frappe.get_doc('Dairy Settings')
		if p_inv.custom_date:
			if p_inv.default_payment_type =='Daily':
				purchase = frappe.db.sql("""select distinct(supplier) as name 
													from `tabPurchase Receipt` 
													where docstatus =1 and posting_date ='{0}'
													""".format(date.today()), as_dict =True)
				for i in purchase:
					milk_entry_li=[]
					pi=frappe.new_doc("Purchase Invoice")			
					me = frappe.db.sql("""select milk_entry
													from `tabPurchase Receipt` 
													where supplier = '{0}' and posting_date = '{1}' and docstatus = 1
													""".format(i.name,date.today()), as_dict =True)
					for m in me:
						milk = frappe.get_doc('Milk Entry',m.milk_entry)
						milk_entry_li.append(str(m.milk_entry))
						ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})
						pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
						if pr:
							pri =  frappe.get_doc('Purchase Receipt',pr)
							pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
							if not pur_inv:
								for itm in pri.items:
									pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
									pi.milk_entry = milk.name
									pi.set_posting_time = 1
									pi.posting_date = p_inv.custom_date
									pi.append(
										"items",
										{
											'item_code': itm.item_code,
											'item_name': itm.item_name,
											'description': itm.description,
											'received_qty': milk.volume,
											'qty': milk.volume,
											'uom': itm.stock_uom,
											'stock_uom': itm.stock_uom,
											'rate': itm.rate,
											'warehouse': milk.dcs_id,
											'purchase_receipt':pr,
											'fat': itm.fat,
											'snf': itm.clr,
											'snf_clr': itm.snf,
											'fat_per': itm.fat_per_ ,
											'snf_clr_per':itm.clr_per ,
											'snf_per':itm.snf_clr_per,
											'milk_entry':milk.name
										}
									)
					bill_wise=0
					per_wise=0
					litre_wise=0
					today=date.today()
					if milk_type == 'Cow':
						item_code = frappe.db.get_single_value("Dairy Settings", "cow_pro")
					elif milk_type == 'Buffalo':
						item_code = frappe.db.get_single_value("Dairy Settings", "buf_pro")
					elif milk_type == 'Mix':
						item_code = frappe.db.get_single_value("Dairy Settings", "mix_pro")
					
					item = frappe.get_doc('Item', item_code)
					milk_item=item.name

					doc_list=frappe.get_all("Standard Deduction",filters={"name":milk.dcs_id,"first_date":['<=',today],"last_date":['>=',today]},fields=["name"])
					if(doc_list):
						get_sd_child = frappe.get_all("child Stand Deduction List", filters={"parent": doc_list[0]['name']},fields=["percentage_wise","bill_wise","litre_wise",
						"cow_item","buffalo_item","mix_item","buffalo_liter_wise","buffalo_percentage_wise","buffalo_bill_wise","mix_liter_wise","mix_percentage_wise","mix_bill_wise","farmer_code","status"])
						for k in get_sd_child:
							if(k.farmer_code== milk.member and k.status==True and milk_item==k.cow_item):
								bill_wise=k.bill_wise
								per_wise=k.percentage_wise
								litre_wise=k.litre_wise
								break
							if(k.farmer_code== milk.member and k.status==True and milk_item==k.buffalo_item):
								bill_wise=k.buffalo_bill_wise
								per_wise=k.buffalo_percentage_wise
								litre_wise=k.buffalo_liter_wise
								break
							if(k.farmer_code== milk.member and k.status==True and milk_item==k.mix_item):
								bill_wise=k.mix_bill_wise
								per_wise=k.mix_percentage_wise
								litre_wise=k.mix_liter_wise
								break

					get_dairy_setting=frappe.get_doc("Dairy Settings")		
					tax_row1 = {
						"charge_type":"Actual",
						"account_head":get_dairy_setting.bill_wise_ded_account,
						"category": "Total",
						"add_deduct_tax": "Deduct",
						"description": "Actual",
						"custom_deduction_types": "Bill Wise",
						"tax_amount": bill_wise
					}
					
					pi.append("taxes", tax_row1)

					tax_row2 = {
						"charge_type": "On Item Quantity",
						"account_head": get_dairy_setting.bill_wise_ded_account,
						"category": "Total",
						"add_deduct_tax": "Deduct",
						"description": "On Item Quantity",
						"custom_deduction_types": "Litre Wise",
						"rate": per_wise
					}
					pi.append("taxes", tax_row2)
					tax_row3 = {
						"charge_type": "On Net Total",
						"account_head": get_dairy_setting.bill_wise_ded_account,
						"category": "Total",
						"add_deduct_tax": "Deduct",
						"description": "On Net Total",
						"custom_deduction_types": "Percentage Wise",
						"rate": litre_wise
					}
		
					pi.append("taxes", tax_row3)

					pi.allocate_advances_automatically=True
					pi.save(ignore_permissions = True)
					pi.submit()
					if (pi.docstatus == 1):
						if(len(milk_entry_li)>=1):
							for i in milk_entry_li:
								milk =frappe.get_doc('Milk Entry',str(i))
								milk.db_set('status','Billed')
					frappe.db.commit()
				p_inv.previous_sync_date=getdate(n_days_ago)
				p_inv.save()



			if p_inv.default_payment_type == 'Days':
				jounral_entry_falg = False
				jounral_entry = frappe.new_doc("Journal Entry")
				jounral_entry.voucher_type = "Journal Entry"
				jounral_entry.posting_date = date.today()
    
				n_days_ago = (datetime.datetime.strptime(p_inv.previous_sync_date,'%Y-%m-%d')) + timedelta(days= p_inv.days-1)
				purchase = frappe.db.sql("""select distinct(supplier) as name 
												from `tabPurchase Receipt` 
												where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
												""".format(p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
				for i in purchase:
					milk_entry_li=[]
					milk_type=""
					me=frappe.db.sql("""select milk_entry , status , supplier
												from `tabPurchase Receipt` 
												where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100 and milk_entry is not null
												""".format(i.name,p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
					if me:
						pi = frappe.new_doc("Purchase Invoice")
						for m in me:
							if m.milk_entry:
								milk =frappe.get_doc('Milk Entry',m.milk_entry)
								milk_entry_li.append(str(m.milk_entry))
								ware =frappe.get_doc('Warehouse',{'name':milk.dcs_id})
								pr =frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
								if pr:
									pri=frappe.get_doc('Purchase Receipt',pr)
									if(pri.custom_milk_type):
										milk_type=pri.custom_milk_type
									pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
									pi.set_posting_time = 1
									# pi.posting_date = p_inv.custom_date
									for itm in pri.items:
										pi.append(
											"items",
											{
												'item_code': itm.item_code,
												'item_name': itm.item_name,
												'description': itm.description,
												'received_qty': milk.volume,
												'qty': milk.volume,
												'uom': itm.stock_uom,
												'stock_uom': itm.stock_uom,
												'rate': itm.rate,
												'warehouse': milk.dcs_id,
												'purchase_receipt':pr,
												'pr_detail':itm.name,
												'fat': itm.fat,
												'snf': itm.clr,
												'snf_clr': itm.snf,
												'fat_per': itm.fat_per_ ,
												'snf_clr_per':itm.clr_per ,
												'snf_per':itm.snf_clr_per,
												'milk_entry':milk.name
											}
										)
						bill_wise=0
						per_wise=0
						litre_wise=0
						milk_item=""
						today=date.today()
						if milk_type == 'Cow':
							item_code = frappe.db.get_single_value("Dairy Settings", "cow_pro")
						elif milk_type == 'Buffalo':
							item_code = frappe.db.get_single_value("Dairy Settings", "buf_pro")
						elif milk_type == 'Mix':
							item_code = frappe.db.get_single_value("Dairy Settings", "mix_pro")
						else:
							frappe.throw("Check Milk Type is set at Purchase Reciept")

						item = frappe.get_doc('Item', item_code)
						milk_item=item.name
						doc_list=frappe.get_all("Standard Deduction",filters={"name":milk.dcs_id,"first_date":['<=',today],"last_date":['>=',today]},fields=["name"])
						if(doc_list):
							get_sd_child = frappe.get_all("child Stand Deduction List", filters={"parent": doc_list[0]['name']},fields=["percentage_wise","bill_wise","litre_wise",
							"cow_item","buffalo_item","mix_item","buffalo_liter_wise","buffalo_percentage_wise","buffalo_bill_wise","mix_liter_wise","mix_percentage_wise","mix_bill_wise","farmer_code","status"])
							
							for k in get_sd_child:
								if(k.farmer_code== milk.member and k.status==True and milk_item==k.cow_item):
									bill_wise=k.bill_wise
									per_wise=k.percentage_wise
									litre_wise=k.litre_wise
									break
								if(k.farmer_code== milk.member and k.status==True and milk_item==k.buffalo_item):
									bill_wise=k.buffalo_bill_wise
									per_wise=k.buffalo_percentage_wise
									litre_wise=k.buffalo_liter_wise
									break
								if(k.farmer_code== milk.member and k.status==True and milk_item==k.mix_item):
									bill_wise=k.mix_bill_wise
									per_wise=k.mix_percentage_wise
									litre_wise=k.mix_liter_wise
									break
						get_dairy_setting=frappe.get_doc("Dairy Settings")
						tax_row1 = {
							"charge_type":"Actual",
							"account_head":get_dairy_setting.bill_wise_ded_account,
							"category": "Total",
							"add_deduct_tax": "Deduct",
							"description": "Actual",
							"custom_deduction_types": "Bill Wise",
							"tax_amount": bill_wise
						}
						pi.append("taxes", tax_row1)

						tax_row2 = {
							"charge_type": "On Item Quantity",
							"account_head": get_dairy_setting.liter_wise_ded_account,
							"category": "Total",
							"add_deduct_tax": "Deduct",
							"description": "On Item Quantity",
							"custom_deduction_types": "Litre Wise",
							"rate":litre_wise
						}

						pi.append("taxes", tax_row2)

						tax_row3 = {
							"charge_type": "On Net Total",
							"account_head": get_dairy_setting.percentage_wise_ded_account,
							"category": "Total",
							"add_deduct_tax": "Deduct",
							"description": "On Net Total",
							"custom_deduction_types": "Percentage Wise",
							"rate": per_wise
						}
						pi.append("taxes", tax_row3)
						pi.save(ignore_permissions = True)
    
						variable_deduction_names = frappe.db.sql("""SELECT name FROM `tabVariable Deduction`
    											WHERE is_deducted = 0 AND date BETWEEN %s AND %s AND farmer_code = %s
            									""",(p_inv.previous_sync_date,getdate(n_days_ago), i.name), as_dict =True)
						variable_deduction = frappe.db.sql("""SELECT SUM(deduction_amount) FROM `tabVariable Deduction`
    											WHERE is_deducted = 0 AND date BETWEEN %s AND %s AND farmer_code = %s
            									""",(p_inv.previous_sync_date,getdate(n_days_ago), i.name), as_dict =True)

						if variable_deduction and variable_deduction[0]['SUM(deduction_amount)']:
							jounral_entry_falg = True
       
							jounral_entry.append("accounts",{
							"account": p_inv.variable_deduction_debit_account,
							"party_type": "Supplier",
							"party": i.name,
							"debit_in_account_currency": round(variable_deduction[0]['SUM(deduction_amount)']),
							"reference_type": "Purchase Invoice",
							"reference_name": pi.name
							})
       
							jounral_entry.append("accounts",{
							"account": p_inv.variable_deduction_credit_account,
							"credit_in_account_currency": round(variable_deduction[0]['SUM(deduction_amount)'])})

						for variable_deduction_name in variable_deduction_names:
							var_doc = frappe.get_doc("Variable Deduction",variable_deduction_name['name'])
							var_doc.is_deducted = 1
							var_doc.save()
						pi.submit()
						frappe.msgprint(str(f"Purchase Invoice Generated {pi.name}"))
						if (pi.docstatus == 1):
							if(len(milk_entry_li)>=1):
								for i in milk_entry_li:
									milk =frappe.get_doc('Milk Entry',str(i))
									milk.db_set('status','Billed')
						frappe.db.commit()
				if jounral_entry_falg:
					jounral_entry.save()
					jounral_entry.submit()
				p_inv.previous_sync_date=getdate(n_days_ago)
				p_inv.save()



			if p_inv.default_payment_type == 'Weekly':
				delta=getdate(today()) - getdate(p_inv.previous_sync_date)
				if delta.days >= 7:
					purchase = frappe.db.sql("""select distinct(supplier) as name 
												from `tabPurchase Receipt` 
												where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
												""".format(p_inv.previous_sync_date,getdate(today())), as_dict =True)
						
				for i in purchase:
					
					me = frappe.db.sql("""select milk_entry , status , supplier
												from `tabPurchase Receipt` 
												where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100
												""".format(i.name,p_inv.previous_sync_date,getdate(today())), as_dict =True)
					if me:
						pi = frappe.new_doc("Purchase Invoice")
						for m in me:
							milk = frappe.get_doc('Milk Entry',m.milk_entry)
							ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

							pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
							if pr:
								pri =  frappe.get_doc('Purchase Receipt',pr)

							# if pr:
								# pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
								# print('pur_inv***************************************',pur_inv)
								# inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["pr_detail"])
								# print('inv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',inv)
								# if not inv:
								
								# pi = frappe.new_doc("Purchase Invoice")
								pi.supplier = milk.member
								pi.set_posting_time = 1
								pi.posting_date = p_inv.custom_date
								# pi.milk_entry = milk.name
								for itm in pri.items:
									# pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
									pi.append(
										"items",
										{
											'item_code': itm.item_code,
											'item_name': itm.item_name,
											'description': itm.description,
											'received_qty': milk.volume,
											'qty': milk.volume,
											'uom': itm.stock_uom,
											'stock_uom': itm.stock_uom,
											'rate': itm.rate,
											'warehouse': milk.dcs_id,
											'purchase_receipt':pr,
											'pr_detail':itm.name,
											'fat': itm.fat,
											'snf': itm.clr,
											'snf_clr': itm.snf,
											'fat_per': itm.fat_per_ ,
											'snf_clr_per':itm.clr_per ,
											'snf_per':itm.snf_clr_per,
											'milk_entry':milk.name
										}
									)
						bill_wise=0
						per_wise=0
						litre_wise=0
						today=date.today()
						doc_list=frappe.get_all("Standard Deduction",filters={"name":milk.dcs_id,"first_date":['<=',today],"last_date":['>=',today]},fields=["name"])
						if(doc_list):
							get_sd_child = frappe.get_all("child Stand Deduction List", filters={"parent": doc_list[0]['name']},fields=["percentage_wise","bill_wise","litre_wise","farmer_code","status"])
							for k in get_sd_child:
								if(k.farmer_code== milk.member and k.status==True):
									bill_wise=k.bill_wise
									per_wise=k.percentage_wise
									litre_wise=k.litre_wise
									break
							
						tax_row1 = {
							"charge_type":"Actual",
							"account_head":"Deduction Payable - BDF",
							"category": "Total",
							"add_deduct_tax": "Deduct",
							"description": "Actual",
							"custom_deduction_types": "Bill Wise",
							"tax_amount": bill_wise
						}

						pi.append("taxes", tax_row1)

						tax_row2 = {
							"charge_type": "On Item Quantity",
							"account_head": "Deduction Payable - BDF",
							"category": "Total",
							"add_deduct_tax": "Deduct",
							"description": "On Item Quantity",
							"custom_deduction_types": "Litre Wise",
							"rate": per_wise
						}

						pi.append("taxes", tax_row2)

						tax_row3 = {
							"charge_type": "On Net Total",
							"account_head": "Deduction Payable - BDF",
							"category": "Total",
							"add_deduct_tax": "Deduct",
							"description": "On Net Total",
							"custom_deduction_types": "Percentage Wise",
							"rate": litre_wise
						}
					
		
						pi.append("taxes", tax_row3)
						# pi.allocate_advances_automatically=True
						pi.save(ignore_permissions = True)
						pi.submit()
						if (pi.docstatus == 1):
							milk.db_set('status','Billed')
				p_inv.db_set('previous_sync_date',getdate(today()))

			

# def purchase_invoice():
	
# 	# tdate = str(date.today())
# 	p_inv = frappe.get_doc('Dairy Settings')
# 	if not p_inv.custom_date:
# 		if p_inv.default_payment_type == 'Daily':
# 			purchase = frappe.db.sql("""select distinct(supplier) as name 
# 												from `tabPurchase Receipt` 
# 												where docstatus =1 and posting_date ='{0}'
# 												""".format(getdate(today())), as_dict =True)
# 			for i in purchase:
# 			# p_inv = frappe.get_doc('Dairy Settings')
# 			# if p_inv.default_payment_type == 'Daily':
# 				pi = frappe.new_doc("Purchase Invoice")
				
				
			
# 				me = frappe.db.sql("""select milk_entry
# 												from `tabPurchase Receipt` 
# 												where supplier = '{0}' and posting_date = '{1}' and docstatus = 1
# 												""".format(i.name,getdate(today())), as_dict =True)
				
# 				for m in me:
# 					milk = frappe.get_doc('Milk Entry',m.milk_entry)
# 					ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

# 					pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])

# 					# for j in pr:
# 					if pr:
# 						pri =  frappe.get_doc('Purchase Receipt',pr)
# 						pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
# 						if not pur_inv:
							
# 							# pi = frappe.new_doc("Purchase Invoice")
# 							for itm in pri.items:
# 								pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
# 								pi.milk_entry = milk.name
# 								pi.append(
# 									"items",
# 									{
# 										'item_code': itm.item_code,
# 										'item_name': itm.item_name,
# 										'description': itm.description,
# 										'received_qty': milk.volume,
# 										'qty': milk.volume,
# 										'uom': itm.stock_uom,
# 										'stock_uom': itm.stock_uom,
# 										'rate': itm.rate,
# 										'warehouse': milk.dcs_id,
# 										'purchase_receipt':pr,
# 										'fat': itm.fat,
# 										'snf': itm.clr,
# 										'snf_clr': itm.snf,
# 										'fat_per': itm.fat_per_ ,
# 										'snf_clr_per':itm.clr_per ,
# 										'snf_per':itm.snf_clr_per,
# 										'milk_entry':milk.name
# 									}
# 								)
# 				pi.save(ignore_permissions = True)
# 				# pi.submit()
# 				if (pi.docstatus == 1):
# 					milk.db_set('status','Billed')



# 		if p_inv.default_payment_type == 'Days':
			
# 			n_days_ago = (datetime.datetime.strptime(p_inv.previous_sync_date,'%Y-%m-%d')) + timedelta(days= p_inv.days-1)
# 			purchase = frappe.db.sql("""select distinct(supplier) as name 
# 											from `tabPurchase Receipt` 
# 											where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
# 											""".format(p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
					
# 			for i in purchase:
				
# 				me = frappe.db.sql("""select milk_entry , status , supplier
# 											from `tabPurchase Receipt` 
# 											where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100 and milk_entry is not null
# 											""".format(i.name,p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
# 				if me:
# 					pi = frappe.new_doc("Purchase Invoice")
# 					print('meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',me)
# 					for m in me:
# 						if m.milk_entry:
# 							milk = frappe.get_doc('Milk Entry',m.milk_entry)
# 							ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

# 							pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
# 							if pr:
# 								pri =  frappe.get_doc('Purchase Receipt',pr)

# 							# if pr:
# 								# pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
# 								# print('pur_inv***************************************',pur_inv)
# 								# inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["pr_detail"])
# 								# print('inv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',inv)
# 								# if not inv:
								
# 								# pi = frappe.new_doc("Purchase Invoice")
# 								pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
# 								# pi.milk_entry = milk.name
# 								for itm in pri.items:
# 									# pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
# 									pi.append(
# 										"items",
# 										{
# 											'item_code': itm.item_code,
# 											'item_name': itm.item_name,
# 											'description': itm.description,
# 											'received_qty': milk.volume,
# 											'qty': milk.volume,
# 											'uom': itm.stock_uom,
# 											'stock_uom': itm.stock_uom,
# 											'rate': itm.rate,
# 											'warehouse': milk.dcs_id,
# 											'purchase_receipt':pr,
# 											'pr_detail':itm.name,
# 											'fat': itm.fat,
# 											'snf': itm.clr,
# 											'snf_clr': itm.snf,
# 											'fat_per': itm.fat_per_ ,
# 											'snf_clr_per':itm.clr_per ,
# 											'snf_per':itm.snf_clr_per,
# 											'milk_entry':milk.name
# 										}
# 									)
# 					pi.save(ignore_permissions = True)
# 					# pi.submit()
# 					if (pi.docstatus == 1):
# 						milk.db_set('status','Billed')
# 					frappe.db.commit()
# 			p_inv.db_set('previous_sync_date',getdate(n_days_ago))




# 	if p_inv.default_payment_type == 'Weekly':
# 		delta=getdate(date.today()) - getdate(p_inv.previous_sync_date)
		
# 		if delta.days >= 7:
# 			purchase = frappe.db.sql("""select distinct(supplier) as name 
# 										from `tabPurchase Receipt` 
# 										where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
# 										""".format(p_inv.previous_sync_date,getdate(today())), as_dict =True)
				
# 		for i in purchase:
			
# 			me = frappe.db.sql("""select milk_entry , status , supplier
# 										from `tabPurchase Receipt` 
# 										where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100
# 										""".format(i.name,p_inv.previous_sync_date,getdate(today())), as_dict =True)
# 			if me:
# 				pi = frappe.new_doc("Purchase Invoice")
# 				for m in me:
# 					milk = frappe.get_doc('Milk Entry',m.milk_entry)
# 					ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

# 					pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
# 					if pr:
# 						pri =  frappe.get_doc('Purchase Receipt',pr)

# 					# if pr:
# 						# pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
# 						# print('pur_inv***************************************',pur_inv)
# 						# inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["pr_detail"])
# 						# print('inv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',inv)
# 						# if not inv:
						
# 						# pi = frappe.new_doc("Purchase Invoice")
# 						pi.supplier = milk.member
# 						# pi.milk_entry = milk.name
# 						for itm in pri.items:
# 							# pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
# 							pi.append(
# 								"items",
# 								{
# 									'item_code': itm.item_code,
# 									'item_name': itm.item_name,
# 									'description': itm.description,
# 									'received_qty': milk.volume,
# 									'qty': milk.volume,
# 									'uom': itm.stock_uom,
# 									'stock_uom': itm.stock_uom,
# 									'rate': itm.rate,
# 									'warehouse': milk.dcs_id,
# 									'purchase_receipt':pr,
# 									'pr_detail':itm.name,
# 									'fat': itm.fat,
# 									'snf': itm.clr,
# 									'snf_clr': itm.snf,
# 									'fat_per': itm.fat_per_ ,
# 									'snf_clr_per':itm.clr_per ,
# 									'snf_per':itm.snf_clr_per,
# 									'milk_entry':milk.name
# 								}
# 							)
# 				pi.save(ignore_permissions = True)
# 				# pi.submit()
# 				if (pi.docstatus == 1):
# 					milk.db_set('status','Billed')
# 		p_inv.db_set('previous_sync_date',getdate(today()))