
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID


class purchase_requisition(osv.osv):

    _inherit = 'purchase.requisition'
    _columns = {
        'calc_sheet_id': fields.many2one('sale.prequotation', 'Calc Sheet No.', required=False, domain=[('state', '=', 'done')]),
        'customer_ref': fields.char('Customer P/O'),
        # Only for TTI, we only allow editing in Draft state
        'date_start': fields.datetime('Requisition Date', readonly=True, states={'draft': [('readonly', False)]}),
        'date_end': fields.datetime('Requisition Deadline', readonly=True, states={'draft': [('readonly', False)]}),
        'user_id': fields.many2one('res.users', 'Responsible', readonly=True, states={'draft': [('readonly', False)]}),
        'exclusive': fields.selection([('exclusive', 'Purchase Requisition (exclusive)'), ('multiple', 'Multiple Requisitions')], 'Requisition Type', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="Purchase Requisition (exclusive):  On the confirmation of a purchase order, it cancels the remaining purchase order.\nPurchase Requisition(Multiple):  It allows to have multiple purchase orders.On confirmation of a purchase order it does not cancel the remaining orders"""),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'line_ids': fields.one2many('purchase.requisition.line', 'requisition_id', 'Products to Purchase', readonly=True, states={'draft': [('readonly', False)]}),
    }

    def _prepare_pr_line(self, product_line):
        res = []
        partner_ids = []
        if product_line.partner_id.id:
            partner_ids = [[6, False, [product_line.partner_id.id]]]
        if product_line.product_id.supply_method == 'bundle':
            for item_line in product_line.product_id.item_ids:
                res.append({'selected_flag': True,
                            'product_id': item_line.item_id.id,
                            'name': item_line.item_id.name,
                            'product_qty': item_line.qty_uom * product_line.product_uom_qty,
                            'product_uom_id': item_line.uom_id.id,
                            'partner_ids': partner_ids})
        else:
            res.append({'selected_flag': True,
                        'product_id': product_line.product_id.id,
                        'name': product_line.name,
                        'product_qty': product_line.product_uom_qty,
                        'product_uom_id': product_line.product_uom.id,
                        'partner_ids': partner_ids})
        return res

    def calc_sheet_id_onchange(self, cr, uid, ids, calc_sheet_id, context=None):
        """ Changes purchase requisition line if Calc Sheet changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        res = {'value': {'line_ids': False}}

        if calc_sheet_id:
            product_lines = []
            calssheet = self.pool.get('sale.prequotation').browse(cr, uid, calc_sheet_id, context=context)
            for line in calssheet.order_line:
                product_lines += self._prepare_pr_line(line)
            for line in calssheet.order_line_labour:
                product_lines += self._prepare_pr_line(line)
            res['value']['line_ids'] = product_lines
            res['value'].update({'all_selected': True})

            # Get SO reference
            if calssheet.mat_sale_id and calssheet.labour_sale_id \
                    and (calssheet.mat_sale_id.id != calssheet.labour_sale_id.id):
                res['value'].update({'ref_sale_order_id': False})
            elif calssheet.mat_sale_id:
                res['value'].update({'ref_sale_order_id': calssheet.mat_sale_id.id})
            elif calssheet.labour_sale_id:
                res['value'].update({'ref_sale_order_id': calssheet.labour_sale_id.id})

        return res

    def _seller_details(self, cr, uid, requisition_line, supplier, context=None):
        pricelist = self.pool.get('product.pricelist')
        product = requisition_line.product_id
        seller_price, qty, default_uom_po_id, date_planned = super(purchase_requisition, self)._seller_details(cr, uid, requisition_line, supplier, context)
        supplier_pricelist = supplier.property_product_pricelist_purchase or False

        seller_price_by_supplier = pricelist.price_get(cr, uid, [supplier_pricelist.id], product.id, qty, supplier.id, {'uom': default_uom_po_id})[supplier_pricelist.id]

        if seller_price_by_supplier:
            seller_price = seller_price_by_supplier

        return seller_price, qty, default_uom_po_id, date_planned

    def tender_cancel(self, cr, uid, ids, context=None):
        for pr in self.browse(cr, uid, ids, context=context):
            if pr.state in ('in_purchase', 'in_progress'):
                if uid != SUPERUSER_ID and not self.pool['res.users'].has_group(cr, uid, 'purchase_requisition.group_purchase_requisition_manager'):
                    raise osv.except_osv(_('Warning!'), _('You are not allowed to cancel this PR. Please contact your Purchase Requisition manager!'))
        return super(purchase_requisition, self).tender_cancel(cr, uid, ids, context=context)

purchase_requisition()


class purchase_requisition_partner(osv.osv_memory):

    _inherit = 'purchase.requisition.partner'

    def _check_partner_duplicate(self, cr, uid, partner_id, rec, context=None):
        # Just skip the validation.
        return True

purchase_requisition_partner()
