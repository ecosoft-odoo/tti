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
from openerp import tools
import math


class sale_order(osv.osv):

    _inherit = "sale.order"

    def _get_quarter_date_order(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            str_quarter = False
            if order.date_order:
                str_quarter = "Quarter %s" % (
                    math.ceil(float(int(order.date_order.split('-')[1])) / 3)
                )
            res[order.id] = str_quarter
        return res

    def _get_year_date_order(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = order.date_order and order.date_order.split('-')[0] or False
        return res

    _columns = {
        'ref_attention_name': fields.char('Attention', size=128, readonly=False),
        'old_quote_number': fields.char('Old Job Number', size=64,),
        'ref_contact2_id': fields.many2one('res.partner', 'Contact 2', domain="[('parent_id','=', partner_id)]", readonly=False),
        'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', readonly=False, required=True, states={'done': [('readonly', True)]}, help="Delivery address for current sales order."),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', change_default=True, required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order."),
        'quarter_date_order': fields.function(_get_quarter_date_order, type='char', string='Order Date - Quarter',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                }),        
        'year_date_order': fields.function(_get_year_date_order, type='char', string='Order Date - Year',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                }),
    }

    _defaults = {
               #'note': "Validity: 30 Days",
               }

    def create(self, cr, uid, data, context=None):
        # Search for default note, if not specified
        if not data.get('note', False):
            ir_values = self.pool.get('ir.values')
            user_obj = self.pool.get('res.users')
            user = user_obj.browse(cr, uid, uid, context=context)
            company_id = user.company_id.id
            condition = 'pricelist_id=' + str(data.get('pricelist_id', False))
            note = ir_values.get_default(
                cr, uid, 'sale.order', 'note', for_all_users=True,
                company_id=company_id, condition=condition)
            data.update({'note': note})
        result = super(sale_order, self).create(cr, uid, data, context=context)
        return result

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


class sale_report(osv.osv):
    _inherit = "sale.report"

    _columns = {
        'brand_id': fields.many2one('product.brand', 'Brand', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_report')
        # TODO: make parent view extensible similarly to invoice analysis and
        #       remove the duplication
        cr.execute("""
            create or replace view sale_report as (
                select
                    min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                    count(*) as nbr,
                    s.date_order as date,
                    s.date_confirm as date_confirm,
                    to_char(s.date_order, 'YYYY') as year,
                    to_char(s.date_order, 'MM') as month,
                    to_char(s.date_order, 'YYYY-MM-DD') as day,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.shop_id as shop_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    s.state,
                    t.categ_id as categ_id,
                    s.shipped,
                    s.shipped::integer as shipped_qty_1,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    p.brand_id as brand_id
                from
                    sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                         left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                group by
                    l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,
                    s.date_confirm,
                    s.partner_id,
                    s.user_id,
                    s.shop_id,
                    s.company_id,
                    s.state,
                    s.shipped,
                    s.pricelist_id,
                    s.project_id,
                    p.brand_id
            )
        """)


sale_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
