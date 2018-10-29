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

import openerp
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class sale_order(osv.osv):

    _inherit = "sale.order"

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _get_pq_margin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for sale in self.browse(cr, uid, ids, context=context):
                res[sale.id] = {
                    'pq_margin': sale.amount_net - (sale.amount_cost + sale.amount_transport + sale.amount_insurance + sale.amount_import_tax),
                    'percent_margin': sale.amount_untaxed and ((sale.amount_net - (sale.amount_cost + sale.amount_transport + sale.amount_insurance + sale.amount_import_tax)) / sale.amount_cost) * 100 or 0.0,
                    'pq_acct_margin': sale.amount_net - sale.amount_cost,
                    'acct_percent_margin': sale.amount_untaxed and ((sale.amount_net - sale.amount_cost) / sale.amount_cost) * 100 or 0.0,
                }
        return res

    def _get_percent_margin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.order_amt and (line.margin / line.order_amt) * 100 or 0.0
        return res

    def action_button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context)
        sale_recs = self.browse(cr, uid, ids, context)
        prequote = self.pool.get('sale.prequotation')

        for sale_rec in sale_recs:
            if not sale_rec.client_order_ref:
                if uid != SUPERUSER_ID and not self.pool['res.users'].has_group(cr, uid, 'sale_prequotation.group_confirm_so_wo_cust_ref'):
                    raise osv.except_osv(_('Warning!'), _('"Customer Reference" is not filled!'))
            if sale_rec.pq_id and sale_rec.pq_id.id:
                prequote.action_button_done(cr, uid, [sale_rec.pq_id.id], context)
        return res

    def _amount_all(self, *args, **kwargs):
        return super(sale_order, self)._amount_all(*args, **kwargs)

    _columns = {
        'pq_id': fields.many2one('sale.prequotation', 'PQ Reference', readonly=True),
        'pq_type': fields.related('pq_id', 'type', type='selection', string='PQ Type', readonly=True,
                                 selection=[
                                    ('trading', 'Trading'),
                                    ('project', 'Project'),
                                    ('calibrate', 'Calibrate'),
                                    ('repair', 'Repair'),
                                    ('rent', 'Rent'),], store=True),
        'doc_version': fields.integer('Version', required=True),
        'pq_margin': fields.function(_get_pq_margin, string='Commission Margin (PQ)',
                store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'amount_total', 'amount_cost', 'add_disc', 'amount_net'], 50),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 50),
                }, multi='margin', help="Margin calculated from Calculation Sheet"),
        'percent_margin': fields.function(_get_pq_margin, string='% Commission Margin (PQ)',
                store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'amount_total', 'amount_cost', 'add_disc', 'amount_net'], 50),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 50),
                }, multi='margin', help="% Margin calculated from Calculation Sheet"),
        'pq_acct_margin': fields.function(_get_pq_margin, string='Accounting Margin (PQ)',
                store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'amount_total', 'amount_cost', 'add_disc', 'amount_net'], 50),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 50),
                }, multi='margin', help="Accounting Margin calculated from Calculation Sheet"),
        'acct_percent_margin': fields.function(_get_pq_margin, string='% Accounting Margin (PQ)',
                store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'amount_total', 'amount_cost', 'add_disc', 'amount_net'], 50),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 50),
                }, multi='margin', help="% Accounting Margin calculated from Calculation Sheet"),
        'overall_product_type': fields.selection([
                ('import', 'Imported'),
                ('domestic', 'Domestic'),
                ('mix', 'Mixed')], string='Overall Product Type', required=True, readonly=False),
        'amount_transport': fields.float(string='Transport Amount', digits_compute=dp.get_precision('Product Price'),),
        'amount_insurance': fields.float(string='Insurance Amount', digits_compute=dp.get_precision('Product Price'),),
        'amount_import_tax': fields.float(string='Import Tax Amount', digits_compute=dp.get_precision('Product Price'),),
        'amount_cost': fields.float(string='Total Cost', digits_compute=dp.get_precision('Product Price'),),
        'amount_net': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Net Amount',
                store={
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'amount_total', 'amount_cost', 'add_disc', 'amount_net'], 30),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 30)
                }, multi='sums', help="The amount after additional discount."),
        'not_used': fields.related('pq_id', 'not_used', type='boolean', string='Not Used', store=True),
    }

    _defaults = {
        'overall_product_type': 'domestic',
        'doc_version': 1
    }

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('doc_version', False):
            if uid != SUPERUSER_ID and not self.pool['res.users'].has_group(cr, uid, 'sale_prequotation.group_revision_quotation'):
                raise openerp.exceptions.AccessError(_("You are not allowed to change the Version, please discard change!"))
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
        return res

sale_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
