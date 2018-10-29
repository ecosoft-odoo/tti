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


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(account_invoice, self).line_get_convert(cr, uid, x, part, date, context=context)
        res.update({'ref_sale_order_id': x.get('ref_sale_order_id', False)})
        return res

account_invoice()


class account_invoice_landedcost_alloc(osv.osv):

    _inherit = 'account.invoice.landedcost.alloc'

    _columns = {
        'ref_sale_order_id': fields.related('supplier_invoice_id', 'ref_sale_order_id', type='many2one', relation='sale.order', string='Ref Sales Order', readonly=True, store=True),
    }

    # Method Overwritten from invoice_landedcost_alloc.account_invoice.py
    def landedcost_move_line_get(self, cr, uid, invoice_id, context=None):

        if context is None:
            context = {}
            
        cur_obj = self.pool.get('res.currency')
        ctx = context.copy()

        res = []
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        ctx.update({'date': inv.date_invoice})
        ctx.update({'pricelist_type': 'purchase'})
        diff_currency_p = inv.currency_id.id <> company_currency

        for line in inv.landedcost_alloc_ids:
            # No amount allocation, continue
            if not line.landedcost_amount_alloc or line.landedcost_amount_alloc == 0:
                continue

            if inv.currency_id.id != company_currency:
                amount_company_currency = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, line.landedcost_amount_alloc, context=ctx)
            else:
                amount_company_currency = line.landedcost_amount_alloc

            sign = 1
            account_id = line.landedcost_account_id.id
            if inv.type in ('out_invoice', 'in_invoice'):
                sign = -1
            else:
                sign = 1

            # Dr
            res.append({
                'type': 'src',
                'name': line.supplier_invoice_id.internal_number,
                'price_unit': -sign * amount_company_currency,
                'quantity': 1.0,
                'price': -sign * amount_company_currency,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
                'amount_currency': diff_currency_p \
                        and line.landedcost_amount_alloc or False,
                'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
                # kittiu
                'ref_sale_order_id': line.supplier_invoice_id.ref_sale_order_id and line.supplier_invoice_id.ref_sale_order_id.id or False,
            })

            # Account Post, Tax
            res.append({
                'type': 'dest',
                'name': line.invoice_id.internal_number,
                'price_unit': sign * amount_company_currency,
                'quantity': 1,
                'price': sign * amount_company_currency,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
                'amount_currency': diff_currency_p \
                        and line.landedcost_amount_alloc or False,
                'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
                # kittiu
                'ref_sale_order_id': line.invoice_id.ref_sale_order_id and line.invoice_id.ref_sale_order_id.id or False,
            })

        return res

account_invoice_landedcost_alloc()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
