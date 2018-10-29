-- General Object
delete from account_billing_line;
delete from account_billing; 
delete from account_invoice_line;
delete from account_invoice;
delete from account_move_line;
delete from account_move;
delete from account_bank_statement_line;
delete from account_bank_statement;
delete from payment_register;
delete from account_voucher_line;
delete from account_voucher;
delete from sale_order_line;
delete from sale_order;
delete from pr_rel_partner;
delete from purchase_order_line;
delete from purchase_order;
delete from purchase_requisition_line;
delete from purchase_requisition;
delete from mrp_production_product_line;
delete from mrp_production;
delete from mrp_bom; -- SQP --> Then re-install the BOM Formula
delete from procurement_order;
delete from stock_move;
delete from stock_picking;
delete from stock_inventory_line;
delete from stock_inventory;
-- TT Tables
delete from sale_prequotation;
delete from sale_prequotation_labour;
delete from sale_prequotation_product;
delete from commission_worksheet;
delete from commission_worksheet_line;
-- Delete workflows
delete from wkf_workitem;
delete from wkf_witm_trans;
delete from wkf_instance;
-- Reset sequence
update ir_sequence set number_next = 1;
-- Reset Postgres Sequence
alter sequence ir_sequence_001 restart with 1;
alter sequence ir_sequence_002 restart with 1;
alter sequence ir_sequence_003 restart with 1;
alter sequence ir_sequence_004 restart with 1;
alter sequence ir_sequence_005 restart with 1;
alter sequence ir_sequence_006 restart with 1;
alter sequence ir_sequence_007 restart with 1;
alter sequence ir_sequence_008 restart with 1;
alter sequence ir_sequence_009 restart with 1;
alter sequence ir_sequence_010 restart with 1;
alter sequence ir_sequence_011 restart with 1;
alter sequence ir_sequence_012 restart with 1;
alter sequence ir_sequence_013 restart with 1;
alter sequence ir_sequence_014 restart with 1;
alter sequence ir_sequence_015 restart with 1;
alter sequence ir_sequence_016 restart with 1;
alter sequence ir_sequence_017 restart with 1;
alter sequence ir_sequence_018 restart with 1;
alter sequence ir_sequence_019 restart with 1;
alter sequence ir_sequence_020 restart with 1;
alter sequence ir_sequence_030 restart with 1;
alter sequence ir_sequence_031 restart with 1;
alter sequence ir_sequence_032 restart with 1;
alter sequence ir_sequence_033 restart with 1;
alter sequence ir_sequence_034 restart with 1;
alter sequence ir_sequence_035 restart with 1;
alter sequence ir_sequence_036 restart with 1;
alter sequence ir_sequence_037 restart with 1;
alter sequence ir_sequence_038 restart with 1;
alter sequence ir_sequence_039 restart with 1;
alter sequence ir_sequence_040 restart with 1;
alter sequence ir_sequence_041 restart with 1;
alter sequence ir_sequence_046 restart with 1;
alter sequence ir_sequence_048 restart with 1;

-- Deleting attachments,
delete from ir_attachment
