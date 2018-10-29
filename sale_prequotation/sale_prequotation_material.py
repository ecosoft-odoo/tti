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


class line_product(osv.osv):
    _name = 'sale.prequotation.product'
    _description = 'Calculation Area MATERIALS'

    def create(self, cr, uid, vals, context=None):
        return super(line_product, self).create(cr, uid, vals, context=context)

    def _get_currency(self, cr, uid, context=None):
        c = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return c

    def _product_uom(self, cr, uid, context=None):
        return False

    def _get_thailand_country(self, cr, uid):
        ir_model_data = self.pool.get('ir.model.data')
        country = ir_model_data.get_object(cr, uid, 'base', 'th')
        return country.id

    def _get_margin(self, cr, uid, ids=False, mtype=False, pq_id=False, context=None):
        if not pq_id:
            if not ids:
                return 0.0
            pq_line = self.browse(cr, uid, [ids[0]], context)
            if not (pq_line and pq_line[0] and pq_line[0].pq_id.id):
                return 0.0

            pq_id = pq_line[0].pq_id.id

        margin_ids = self.pool.get('sale.profit.margin').search(cr, uid, [('prequote_id', '=', pq_id), ('name', '=', mtype)])
        if margin_ids:
            m = self.pool.get('sale.profit.margin').browse(cr, uid, margin_ids[0], context)
            if m and m.percentage:
                return m.percentage
            return 0.0
        else:
            return 0.0

    def onchange_type(self, cr, uid, ids, type, import_tax, context):
        res = {}
        if type == "import":
            res = {'value': {'percentage': import_tax}}
        else:
            res = {'value': {'percentage': 0}}
        return res

    def onchange_product_category(self, cr, uid, ids, category_id=False, context=None):
        if category_id:
            res = {'domain': {'product_id': [('sale_ok', '=', True), ('categ_id', '=', category_id)]}}
        else:
            res = {'domain': {'product_id': [('sale_ok', '=', True)]}}
        return res

    def onchange_product_id(self, cr, uid, ids, product_id, qty=False, uom_id=False, partner_id=False, currency_id=False, cal_date=False, import_tax=False, pricelist_id=False, context=None):
        if context is None:
            context = {}
        res = {'value': {'name': '', 'cost_price_unit': 0.0, 'product_uom': uom_id, 'product_uom_qty': 1, 'partner_id': False, 'percentage': 0.0}}
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
                    if (qty or 0.0) < min_qty:  # If the supplier quantity is greater than entered from user, set minimal.
                        if qty:
                            res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                        qty = min_qty
        qty = qty or 1.0
        if qty:
            res['value'].update({'product_uom_qty': qty})
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
        if context.get('partner_changed', False):
            res['value'].update({'partner_id': partner_id})
            # if partner.country_id and partner.country_id.id and partner.country_id.id == self._get_thailand_country(cr, uid):
            if (1 in [x.id for x in partner.category_id]):  # Domestic = 1
                res['value'].update({'type': 'domestic'})
                res['value'].update({'percentage': 0.00})
            else:
                if partner.country_id and partner.country_id.id:
                    res['value'].update({'type': 'import'})
                    res['value'].update({'percentage': import_tax})
        else:
            res['value'].update({'partner_id': product.seller_id.id})
            #if product.seller_id and product.seller_id.country_id and product.seller_id.country_id.id == self._get_thailand_country(cr, uid):
            if product.seller_id and (1 in [x.id for x in product.seller_id.category_id]):  # Oversea = 2
                res['value'].update({'type': 'domestic'})
                res['value'].update({'percentage': 0.00})
            else:
                if product.seller_id and product.seller_id.country_id:
                    res['value'].update({'type': 'import'})
                    res['value'].update({'percentage': import_tax})
        res['value'].update({'currency_id': price_currency_id})
        res['value'].update({'cost_price_unit': price})
        dom = {'partner_id': [('id', 'in', sale_prequotation.get_product_supplier_list(cr, uid, product_id))]}
        res['domain'].update(dom)
        return res

    def partner_id_change(self, cr, uid, ids, product_id, partner_id, currency_id=False, cal_date=False, import_tax=False, context=None):
        if not context:
            context = {}
        pricelist_id = False
        if partner_id:
            partner = self.pool.get('res.partner')
            supplier = partner.browse(cr, uid, partner_id)
            pricelist_id = supplier.property_product_pricelist_purchase.id
        context.update({'partner_changed': True})
        return self.onchange_product_id(cr, uid, ids=ids, product_id=product_id, pricelist_id=pricelist_id, partner_id=partner_id, currency_id=currency_id, cal_date=cal_date, import_tax=import_tax, context=context)

    def onchange_product_uom_qty(self, cr, uid, ids, product_id, qty=False, uom_id=False, partner_id=False, currency_id=False, cal_date=False, import_tax=False, pricelist_id=False, context=None):
        if not context:
            context = {}
        if partner_id:
            context.update({'partner_changed': True})  # Set as if this is partner changed, so that the partner will not be reset to default.
        return self.onchange_product_id(cr, uid, ids, product_id, qty=qty, uom_id=uom_id, partner_id=partner_id, currency_id=currency_id, cal_date=cal_date, import_tax=import_tax, pricelist_id=pricelist_id, context=context)

    def _get_profit(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = 0.0
            if line.type == 'import':
                p = self._get_margin(cr, uid, [line.id], 'Profit Margin Import(%)', context=context)
                res[line.id] = (line.price_unit * p) / 100
            else:
                p = self._get_margin(cr, uid, [line.id], 'Profit Margin Domestic(%)', context=context)
                res[line.id] = (line.price_unit * p) / 100
        return res

    def _get_transport(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = 0.0
            if line.type == 'import':
                p = self._get_margin(cr, uid, [line.id], 'Transport Margin Import(%)', context=context)
                res[line.id] = (line.price_unit * p) / 100
            else:
                p = self._get_margin(cr, uid, [line.id], 'Transport Margin Domestic(%)', context=context)
                res[line.id] = (line.price_unit * p) / 100
        return res

    def _get_insurance(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = 0.0
            if line.type == 'import':
                p = self._get_margin(cr, uid, [line.id], 'Insurance Margin Import(%)', context=context)
                res[line.id] = (line.price_unit * p) / 100
            else:
                res[line.id] = 0
        return res

    def _compute_import_tax(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = 0.0
            if line.type == 'import':
                p = line.percentage
                res[line.id] = (line.price_unit * p) / 100
        return res

    def _get_import_tax(self, cr, uid, ids, context=None):
        return self._get_margin(cr, uid, ids, 'Import Tax(%)', context=context)

    def _get_price_unit(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        ctx = context.copy()
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            ctx.update({'date': line.pq_id.cal_date})
            amount = line.cost_price_unit - line.cost_price_unit * line.discount / 100
            amount_currency = cur_obj.compute_rate_calc(cr, uid, line.currency_id.id, line.pq_id.currency_id.id, amount, context=ctx)
            res[line.id] = amount_currency
        return res

    def _get_price_unit_sale(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.profit + line.transport + line.insurance + line.import_tax + line.price_unit
        return res

    def _get_price_unit_sale_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.price_unit_sale
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.prequotation').browse(cr, uid, ids, context=context):
            for l in line.order_line:
                result[l.id] = True
        return result.keys()

    def _get_profit_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.profit
        return res

    def _get_transport_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.transport
        return res

    def _get_insurance_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.insurance
        return res

    def _get_import_tax_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.import_tax
        return res

    def _get_price_unit_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not hasattr(line, 'pq_id'):
                continue
            res[line.id] = line.product_uom_qty * line.price_unit
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(line_product, self).view_init(cr, uid, fields_list, context=context)
        if not res:
            res = {}
        res.update({'domain': {'product_id': [('sale_ok', '=', True)]}})
        return res

    #Overriding from line_product Class
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        result = super(line_product, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        return result

    _columns = {
        'pq_id': fields.many2one('sale.prequotation', 'PreQuotation Reference', required=True, ondelete='cascade', select=True, readonly=False),
        'name': fields.text('Description', required=True, readonly=False),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'category_id': fields.many2one('product.category', 'Product Category', help="Specify a product category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise."),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),
        'partner_id': fields.many2one('res.partner', 'Supplier', readonly=False),
        'product_uom_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoS'), required=True, readonly=False),
        'product_uom': fields.many2one('product.uom', 'UOM', help="Unit of Measure", required=True, readonly=False),
        'cost_price_unit': fields.float('Unit Cost Purchase', required=True, digits_compute=dp.get_precision('Product Price'), readonly=False),
        'discount': fields.float('Disc(%)', digits_compute=dp.get_precision('Discount')),
        'sale_currency_id': fields.related('pq_id', 'currency_id', type='many2one', relation='res.currency', string="Currency", readonly=True, required=False),
        'currency_id': fields.many2one('res.currency', string="Currency", required=True,),
        'type': fields.selection([('import', 'Imported'),
                                  ('domestic', 'Domestic')], string='Type', required=True, readonly=False),
        'percentage': fields.float('Import Tax (%)', digits=(16, 2), required=True, help='Give percentage value between 0-100.'),
        'price_unit': fields.function(_get_price_unit, string='Unit Cost', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 3),
                'sale.prequotation': (_get_order, [], 3),
            }),
        'profit': fields.function(_get_profit, string='Profit', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            }),
        'transport': fields.function(_get_transport, string='Transport', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            }),
        'insurance': fields.function(_get_insurance, string='Insurance', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            }),
        'import_tax': fields.function(_compute_import_tax, string='Import Tax', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            }),
        'profit_total': fields.function(_get_profit_total, string='Total Profit', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            }),
        'transport_total': fields.function(_get_transport_total, string='Total Transport', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            }),
        'insurance_total': fields.function(_get_insurance_total, string='Total Insurance', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                'sale.prequotation': (_get_order, [], 4),
            }),
        'import_tax_total': fields.function(_get_import_tax_total, string='Total Import Tax', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 5),
                'sale.prequotation': (_get_order, [], 5),
            }),
        'price_unit_sale': fields.function(_get_price_unit_sale, string='Unit Price Selling', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                'sale.prequotation': (_get_order, [], 10),
            }),
        'price_unit_total': fields.function(_get_price_unit_total, string='Total Cost', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                'sale.prequotation': (_get_order, [], 10),
            }),
        'price_unit_sale_total': fields.function(_get_price_unit_sale_total, string='Total Price Selling', required=False, digits_compute=dp.get_precision('Product Price'),
            store={
                'sale.prequotation.product': (lambda self, cr, uid, ids, c={}: ids, [], 15),
                'sale.prequotation': (_get_order, [], 15),
            }),
        'company_id': fields.related('pq_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
    }
    _defaults = {
        'product_uom': _product_uom,
        'category_id': False,
    }
line_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
