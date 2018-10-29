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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class sale_order(osv.osv):

    _inherit = "sale.order"
    _columns = {
        'ref_attention_name': fields.char('Attention', size=128, readonly=False),
        'old_quote_number': fields.char('Old Job Number', size=64,),
        'ref_contact2_id': fields.many2one('res.partner', 'Contact 2', domain="[('parent_id','=', partner_id)]", readonly=False),
        'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', readonly=False, required=True, states={'done': [('readonly', True)]}, help="Delivery address for current sales order."),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', change_default=True, required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order."),
    }

    _defaults = {
               #'note': "Validity: 30 Days",
               }

    def action_button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context)
        line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', 'in', ids), ('delivery_date', '=', False)])
        if line_ids:
            raise osv.except_osv(_('Error!'),
                                _('Some product line do not have Delivery Date!'))
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Error!'),
                            _('Duplication of Quotation/Sales Order is not allowed, please use Calculation Sheet!'))

sale_order()


class sale_order_line(osv.osv):

    _inherit = 'sale.order.line'
    _columns = {
                'delivery_date': fields.char('Delivery Date', readonly=False),
                'expected_delivery_date': fields.date('Expected Delivery Date'),
                'pq_id': fields.related('order_id', 'pq_id', type="many2one", relation="sale.prequotation", string="Calc No.", readonly=True, store=False)
    }

    def onchange_expected_delivery_date(self, cr, uid, ids, date_order, delay, expected_delivery_date, context=None):
        if not date_order:
            return False
        date_order = datetime.strptime(date_order, '%Y-%m-%d')
        expected_delivery_date = datetime.strptime(expected_delivery_date, '%Y-%m-%d')
        diff = expected_delivery_date - date_order
        diff.days
        return {'value': {'delay': diff.days}}

    def onchange_delay(self, cr, uid, ids, date_order, delay, expected_delivery_date, context=None):
        if not date_order:
            return False
        date_order = datetime.strptime(date_order, '%Y-%m-%d')
        expected_delivery_date = date_order + relativedelta(days=delay)
        return {'value': {'expected_delivery_date': expected_delivery_date.strftime('%Y-%m-%d')}}

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
