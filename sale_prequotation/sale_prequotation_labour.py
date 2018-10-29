# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
import sale_prequotation
from openerp.tools.translate import _


class line_labour(osv.osv):
    _name = 'sale.prequotation.labour'
    _description = 'Calculation Area LABOUR'

    def write(self, cr, uid, ids, vals, context=None):
        return super(line_labour, self).write(cr, uid, ids, vals, context=context)

    def onchange_product_category(self, cr, uid, ids, labour_category_id, category_id=False, context=None):
        if category_id:
            res = {'domain': {'product_id': [('sale_ok', '=', True), ('type', '=', 'service'), ('categ_id', '=', category_id)]}}
        else:
            res = {'domain': {'product_id': [('sale_ok', '=', True), ('type', '=', 'service'), ('categ_id', 'child_of', [labour_category_id])]}}
        return res

    def onchange_product_id(self, cr, uid, ids, product_id, qty=False, uom_id=False, partner_id=False, currency_id=False, cal_date=False, import_tax=False, pricelist_id=False, context=None):
        if not context:
            context = {}
        res = {'value': {'name': '', 'cost_price_unit': 0.0, 'product_uom': uom_id, 'product_uom_qty': 1, 'partner_id': False}}
        if not product_id:
            return res
        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        context_partner = context.copy()
        if partner_id:
            partner = res_partner.browse(cr, uid, partner_id)
            lang = partner.lang
            pricelist_id = partner.property_product_pricelist_purchase.id
            context_partner.update({'lang': lang, 'partner_id': partner_id})
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
        if product.description_sale:
            name += '\n' + product.description_sale
        elif product.description:
            name += '\n' + product.description
        res['value'].update({'name': name})
        res['domain'] = {'product_uom': [('category_id', '=', product.uom_id.category_id.id)]}
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id
        res['value'].update({'product_uom': uom_id})
        if partner_id:
            supplierinfo = False
            for supplier in product.seller_ids:
                if supplier.name.id == partner_id:
                    supplierinfo = supplier
                    if supplierinfo.product_uom.id != uom_id:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name}
                    min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                    # If the supplier quantity is greater than entered from user, set minimal.
                    if (qty or 0.0) < min_qty:
                        if qty:
                            res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                        qty = min_qty
        qty = qty or 1.0
        if qty:
            res['value'].update({'product_qty': qty})
        price = False
        price_currency_id = self._get_currency(cr, uid, context)
        if pricelist_id:
            price = product_pricelist.price_get(cr, uid, [pricelist_id],
                    product.id, qty or 1.0, partner_id or False, {'uom': uom_id})[pricelist_id]
            price_currency_id = product_pricelist.browse(cr, uid, pricelist_id, context=context).currency_id.id
        if not price:
            price = product.standard_price
        if product and product.categ_id and product.categ_id.id:
            res['value'].update({'category_id': product.categ_id.id})
        res['value'].update({'currency_id': price_currency_id})
        res['value'].update({'cost_price_unit': price})
        res['value'].update({'partner_id': product.seller_id.id})
        # Dynamic domain filter for partner_id
        dom = {'partner_id': [('id', 'in', sale_prequotation.get_product_supplier_list(cr, uid, product_id))]}
        res['domain'].update(dom)
        return res

    def partner_id_change(self, cr, uid, ids, product_id, partner_id, currency_id=False, cal_date=False, import_tax=False, context=None):
        pricelist_id = False
        if partner_id:
            partner = self.pool.get('res.partner')
            supplier = partner.browse(cr, uid, partner_id)
            pricelist_id = supplier.property_product_pricelist_purchase.id
        return self.onchange_product_id(cr, uid, ids=ids, product_id=product_id, pricelist_id=pricelist_id, partner_id=partner_id, currency_id=currency_id, cal_date=cal_date, import_tax=import_tax, context=context)

    def _get_currency(self, cr, uid, context=None):
        c = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return c

    def _product_uom(self, cr, uid, context=None):
        uoms = self.pool.get('product.uom').search(cr, uid, [('name', 'ilike', 'Hour')])
        return uoms and uoms[0] or False

#     def _default_category(self, cr, uid, context=None):
#         md = self.pool.get('ir.model.data')
#         res = md.get_object_reference(cr, uid, "", 'Labour')
#         return res[1]

    def _default_labour_category(self, cr, uid, context=None):
        cat_obj = self.pool.get('product.category')
        ids = cat_obj.search(cr, uid, [('name', '=', 'Labour')])  # Fixed to "Labour"
        return ids and ids[0] or 0

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.prequotation').browse(cr, uid, ids, context=context):
            for l in line.order_line_labour:
                result[l.id] = True
        return result.keys()

    def _get_profit(self, cr, uid, ids, name, args, context=None):
        res = {}
        p = 0.0
        margin_ids = False
        if ids:
            pq_line = self.read(cr, uid, [ids[0]], ['pq_id'], context)
            if (pq_line and pq_line[0] and pq_line[0]['pq_id'][0]):
                margin_ids = self.pool.get('sale.profit.margin').search(cr, uid, [('prequote_id', '=', pq_line[0]['pq_id'][0]), ('name', '=', 'Profit Margin Labour(%)')])

        if margin_ids:
            m = self.pool.get('sale.profit.margin').browse(cr, uid, margin_ids[0], context)
            p = m.percentage
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = (line.price_unit * p) / 100
        return res

    def _get_priceunit(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        ctx = context.copy()
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            ctx.update({'date': line.pq_id.cal_date})
            amount_currency = cur_obj.compute_rate_calc(cr, uid, line.currency_id.id, line.pq_id.currency_id.id, line.cost_price_unit, context=ctx)
            res[line.id] = amount_currency
        return res

    def _get_price_unit_sale(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.profit + line.price_unit
        return res

    def _get_price_unit_sale_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.price_unit_sale
        return res

    def _get_profit_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.profit
        return res

    def _get_priceunit_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.price_unit
        return res

    _columns = {
        'pq_id': fields.many2one('sale.prequotation', 'PreQuotation Reference', required=True, ondelete='cascade', select=True, readonly=False),
        'name': fields.text('Description', required=True, readonly=False),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        # Category and Product will be under Category "Labour" (767)
        'labour_category_id': fields.many2one('product.category', 'Labour Category'),
        'category_id': fields.many2one('product.category', 'Product Category', domain="[('id','child_of',[labour_category_id])]", help="Specify a product category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise."),
        'product_id': fields.many2one('product.product', 'Product', domain="[('sale_ok', '=', True), ('categ_id','child_of',[labour_category_id])]", change_default=True),
        'partner_id': fields.many2one('res.partner', 'Supplier', readonly=False),
        'product_uom_qty': fields.float('Qty Man Hour', help='Quantity Man Hour', digits_compute=dp.get_precision('Product UoS'), required=True, readonly=False),
        'product_uom': fields.many2one('product.uom', 'UOM', help='Unit of Measure ', required=True, readonly=False),
        'cost_price_unit': fields.float('Unit Cost Purchase', required=True, digits_compute=dp.get_precision('Product Price'), readonly=False),
        'sale_currency_id': fields.related('pq_id', 'currency_id', type='many2one', relation='res.currency', string="Currency", readonly=True, required=False),
        'currency_id': fields.many2one('res.currency', string="Currency", required=True,),
        'price_unit': fields.function(_get_priceunit, string='Unit Cost', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.labour': (lambda self, cr, uid, ids, c={}: ids, [], 3),
                'sale.prequotation': (_get_order, [], 3),
            },),
        'price_unit_total': fields.function(_get_priceunit_total, string='Total Labour Cost', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.labour': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            },),
        'profit': fields.function(_get_profit, string='Profit', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.labour': (lambda self, cr, uid, ids, c={}: ids, [], 5),
                'sale.prequotation': (_get_order, [], 5),
            },),
        'price_unit_sale': fields.function(_get_price_unit_sale, string='Unit Price Selling', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.labour': (lambda self, cr, uid, ids, c={}: ids, [], 6),
                'sale.prequotation': (_get_order, [], 6),
            },),
        'price_unit_sale_total': fields.function(_get_price_unit_sale_total, string='Total Price Selling', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.labour': (lambda self, cr, uid, ids, c={}: ids, [], 7),
                'sale.prequotation': (_get_order, [], 7),
            },),
        'profit_total': fields.function(_get_profit_total, string='Total Profit', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.labour': (lambda self, cr, uid, ids, c={}: ids, [], 8),
                'sale.prequotation': (_get_order, [], 8),
            },),
        'company_id': fields.related('pq_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
    }
    _defaults = {
        'product_uom': _product_uom,
        'labour_category_id': _default_labour_category,
    }

line_labour()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
