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
from openerp import SUPERUSER_ID
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc

NUMBER_TO_CHAR = {
    1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J',
    11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T',
    21: 'U', 22: 'V', 23: 'W', 24: 'X', 25: 'Y', 26: 'Z'
}


def get_product_supplier_list(cr, uid, product_id, context=None):
    supplier_list = []
    cr.execute("""
        select name from product_supplierinfo psi
        join product_product pp on product_tmpl_id = psi.product_id
        where pp.id = %s
        order by sequence
    """, (product_id,))
    res = cr.fetchall()
    for r in res:
        supplier_list.append(r[0])
    return supplier_list and supplier_list or False


class margin_rate(osv.osv):
    _name = "margin.rate"
    _description = "Margin Rate"
    _order = "name desc"
    _columns = {
        'name': fields.date('Date', required=True, select=True),
        'rate': fields.float('Rate', digits=(12, 6), help='Give percentage value between 0-100.'),
        'margin_id': fields.many2one('sale.margin.master', 'Margin', readonly=True),
    }


class sale_margin_master(osv.osv):

    def _current_rate(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        date = time.strftime('%Y-%m-%d')
        for id in ids:
            cr.execute("SELECT margin_id, rate FROM margin_rate WHERE margin_id = %s AND name <= %s ORDER BY name desc LIMIT 1", (id, date))
            res[id] = 0.0
            if cr.rowcount:
                id, rate = cr.fetchall()[0]
                res[id] = rate
        return res

    _name = 'sale.margin.master'
    _description = 'Margin Master'
    _columns = {
        'name': fields.char('Name', required=True, size=256),
        'rate_ids': fields.one2many('margin.rate', 'margin_id', 'Rates'),
        'latest_rate': fields.function(_current_rate, string='Latest Rate', digits=(12, 6),
                                       help='The rate of the margin as of current date.'),
    }


class sale_profit_margin(osv.osv):
    _name = 'sale.profit.margin'
    _description = 'Margin Used in Prequotation'
    _columns = {
        'name': fields.char('Name', required=True, size=256),
        'percentage': fields.float('Rate', digits=(12, 6), help='Give percentage value between 0-100.'),
        'prequote_id': fields.many2one('sale.prequotation', 'quote', readonly=True),
        'margin_id': fields.many2one('sale.margin.master', 'Margin', readonly=True),
    }


class sale_prequotation(osv.osv):
    _name = 'sale.prequotation'
    _description = 'Sales PreQuotation'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _update_product_type(self, cr, uid, ids, vals, context=None):
        for id in ids:
            cr.execute('SELECT distinct type '\
                        'FROM sale_prequotation_product '\
                        'WHERE pq_id = %s ', (id,))
            types = cr.fetchall()
            if len(types) > 1:
                cr.execute('update sale_prequotation set overall_product_type = %s '\
                           'WHERE id = %s ', ('mix', id,))
            elif len(types) == 1:
                cr.execute('update sale_prequotation set overall_product_type = %s '\
                           'WHERE id = %s ', (types[0][0], id,))

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.prequotation') or '/'
        res_id = super(sale_prequotation, self).create(cr, uid, vals, context=context)
        self._update_product_type(cr, uid, [res_id], vals, context)
        return res_id

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'date_pq': time.strftime('%Y-%m-%d'),
            'cal_date': time.strftime('%Y-%m-%d'),
            'state': 'draft',
            'user_id': uid,
            'sale_ids': False,
            'mat_sale_id': None,
            'labour_sale_id': None,
            'doc_version': 0,
            'mat_sale_no': False,
            'labour_sale_no': False,
            'pq_history_ids': False,
            'name': self.pool.get('ir.sequence').get(cr, uid, 'sale.prequotation') or '/',
        })
        return super(sale_prequotation, self).copy(cr, uid, id, default, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'not_used' in vals:  # If not used is checked, also update the same to SOs
            [{'id': 832, 'labour_sale_id': False, 'mat_sale_id': (1413, u'SO1408/0192')}]
            results = self.read(cr, uid, ids, ['mat_sale_id', 'labour_sale_id'], context=context)
            sale_ids = []
            not_used = vals.get('not_used', False)
            for result in results:
                if result['mat_sale_id']:
                    sale_ids.append(result['mat_sale_id'][0])
                if result['labour_sale_id']:
                    sale_ids.append(result['labour_sale_id'][0])
            cr.execute('update sale_order set not_used=%s where id in %s', (not_used, tuple(sale_ids),))
        res = super(sale_prequotation, self).write(cr, uid, ids, vals, context=context)
        self._update_product_type(cr, uid, ids, vals, context)
        return res

    def action_button_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'})

    def action_button_confirm(self, cr, uid, ids, context=None):
        # Allow confirm for specific type only Engineer
        for pq in self.browse(cr, uid, ids, context=context):
            if pq.type in ('project', 'calibrate', 'repair'):
                if uid != SUPERUSER_ID and not self.pool['res.users'].has_group(cr, uid, 'sale_prequotation.group_sale_engineer'):
                    raise osv.except_osv(_('Warning!'), _('Only engineers are allowed to confirm this Calculation Sheet!'))
        return self.write(cr, uid, ids, {'state': 'confirm'})

    def action_button_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'})

    def action_button_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'})

    def _get_pq(self, cr, uid, ids, context=None):
        return ids

    def _get_order_pq(self, cr, uid, ids, context=None):
        result = {}
        for order in self.pool.get('sale.order').browse(cr, uid, ids, context=context):
            result[order.pq_id.id] = True
        return result.keys()

    def _get_products(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.prequotation.product').browse(cr, uid, ids, context=context):
            result[line.pq_id.id] = True
        return result.keys()

    def _get_labour(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.prequotation.labour').browse(cr, uid, ids, context=context):
            result[line.pq_id.id] = True
        return result.keys()

    def _get_convert_rate(self, cr, uid, ids, name, args, context=None):
        res = {}.fromkeys(ids, 0.0)
        convert_state = ('progress', 'manual', 'done')
        for pq in self.browse(cr, uid, ids, context=context):
            res[pq.id] = {
                'convert_rate': 0.0,
                'convert_amount': 0.0,
            }
            convert_rate = 0.0
            convert_amount = 0.0
            if pq.mat_sale_id and pq.labour_sale_id and (pq.mat_sale_id != pq.labour_sale_id):  # 2 SOs
                if pq.mat_sale_id.state in convert_state:
                    convert_rate += 50.0
                    convert_amount += pq.mat_sale_id.amount_net
                if pq.labour_sale_id.state in convert_state:
                    convert_rate += 50.0
                    convert_amount += pq.labour_sale_id.amount_net
            elif pq.mat_sale_id and pq.labour_sale_id and (pq.mat_sale_id == pq.labour_sale_id):  # 1 SO for both
                if pq.mat_sale_id.state in convert_state:
                    convert_rate = 100.0
                    convert_amount += pq.mat_sale_id.amount_net
            elif pq.mat_sale_id and not pq.labour_sale_id:  # Only Material
                if pq.mat_sale_id.state in convert_state:
                    convert_rate = 100.0
                    convert_amount += pq.mat_sale_id.amount_net
            elif not pq.mat_sale_id and pq.labour_sale_id:  # Only Labour
                if pq.labour_sale_id.state in convert_state:
                    convert_rate = 100.0
                    convert_amount += pq.labour_sale_id.amount_net
            res[pq.id]['convert_rate'] = convert_rate
            res[pq.id]['convert_amount'] = convert_amount
        return res

    def _get_import_tax(self, cr, uid, ids, name, args, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        import_tax_id = ir_model_data.get_object(cr, uid, 'sale_prequotation', 'import_tax')

        res = {}.fromkeys(ids, 0.0)
        for pq in self.browse(cr, uid, ids, context=context):
            if pq.margins:
                for margin in pq.margins:
                    if margin.margin_id.id == import_tax_id.id:
                        res[pq.id] = margin.percentage
            else:
                if context is None:
                    context = {}
                date = pq.cal_date or time.strftime('%Y-%m-%d')
                cr.execute("SELECT  rate FROM margin_rate WHERE margin_id = %s AND name <= %s ORDER BY name desc LIMIT 1", (import_tax_id.id, date))
                res[id] = 0.0
                if cr.rowcount:
                    rec = cr.fetchall()
                    res[pq.id] = rec[0][0]
        return res

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pq in self.browse(cr, uid, ids, context=context):
            res[pq.id] = {
                'amount_material_cost': 0.0,
                'amount_labour_cost': 0.0,
                'amount_cost_total': 0.0,
                'amount_material_sale': 0.0,
                'amount_labour_sale': 0.0,
                'amount_unforeseen': 0.0,
                'amount_transport': 0.0,  # to_exclude
                'amount_insurance': 0.0,  # to_exclude
                'amount_import_tax': 0.0,  # to_exclude
                'amount_sale_total': 0.0,
                'margin': 0.0,
                'margin_percent': 0.0
            }
            for line in pq.order_line:
                res[pq.id]['amount_material_cost'] += line.price_unit_total  # material sum
                res[pq.id]['amount_material_sale'] += line.price_unit_sale_total  # material sum
            for line in pq.order_line_labour:
                res[pq.id]['amount_labour_cost'] += line.price_unit_total  # labour sum
                res[pq.id]['amount_labour_sale'] += line.price_unit_sale_total  # labour sum
            res[pq.id]['amount_cost_total'] = res[pq.id]['amount_material_cost'] + res[pq.id]['amount_labour_cost'] + pq.customer_commission
            res[pq.id]['amount_unforeseen'] = res[pq.id]['amount_material_cost'] * (pq.percent_unforeseen / 100)
            res[pq.id]['amount_transport'] = sum([line.transport_total for line in pq.order_line])  # to_exclude
            res[pq.id]['amount_insurance'] = sum([line.insurance_total for line in pq.order_line])  # to_exclude
            res[pq.id]['amount_import_tax'] = sum([line.import_tax_total for line in pq.order_line])  # to_exclude
            res[pq.id]['amount_sale_total'] = res[pq.id]['amount_material_sale'] + res[pq.id]['amount_labour_sale'] + res[pq.id]['amount_unforeseen']
            # Account Margin, include transport, insurance, import_tax margin
            res[pq.id]['acct_margin'] = res[pq.id]['amount_sale_total'] - res[pq.id]['amount_cost_total']
            res[pq.id]['acct_margin_percent'] = res[pq.id]['amount_cost_total'] and (res[pq.id]['acct_margin'] / res[pq.id]['amount_cost_total']) * 100 or 0.0
            # Commission Margin, exclude transport, import_tax, insurance margin -- to_excluude
            res[pq.id]['margin'] = res[pq.id]['amount_sale_total'] - (res[pq.id]['amount_cost_total'] + res[pq.id]['amount_transport'] + res[pq.id]['amount_insurance'] + res[pq.id]['amount_import_tax'])
            res[pq.id]['margin_percent'] = res[pq.id]['amount_cost_total'] and (res[pq.id]['margin'] / res[pq.id]['amount_cost_total']) * 100 or 0.0
        return res

    def _get_currency(self, cr, uid, context=None):
        c = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return c

    def _get_year_pq(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pq in self.browse(cr, uid, ids, context=context):
            res[pq.id] = pq.date_pq.split('-')[0]
        return res

    _columns = {
        'name': fields.char('Calc Sheet Number', size=64, required=True,
            readonly=True, states={'draft': [('readonly', False)]}, select=True),
        'date_pq': fields.date('Calc sheet Date', required=True, readonly=True, select=True,
                               states={'draft': [('readonly', False)]}, track_visibility='always'),
        'year_pq': fields.function(_get_year_pq, type='char', string='Years',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                }),
        'pq_id': fields.many2one('sale.prequotation', 'PreQuotation Reference'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('cancel', 'Cancelled'),
            ('confirm', 'Confirmed'),
            ('done', 'Sale Order Created')
            ], 'Status', readonly=True,
             select=True, track_visibility='always',),
        'partner_id': fields.many2one('res.partner', 'Customer', domain=[('customer', '=', True), ('is_company', '=', True)], required=False, readonly=True,
                                      states={'draft': [('readonly', False)], 'confirm': [('readonly', False), ('required', True)]},
                                      select=True, track_visibility='always'),
        #'partner_contact_id': fields.char('Contact Person Customer', size=128, required=False, states={'confirm': [('required', True)]}),
        'sale_ids': fields.one2many('sale.order', 'pq_id', 'Calculation Sheet', readonly=True),
        'pq_history_ids': fields.one2many('sale.prequotation', 'pq_id', 'PQ History'),
        'split_flag': fields.boolean(string='Split Material/Labour Quotation',),
        'mat_sale_id': fields.many2one('sale.order', 'Quote Ref of Material', readonly=True),
        'labour_sale_id': fields.many2one('sale.order', 'Quote Ref of Labour', readonly=True),
        'mat_sale_no': fields.char('Quote No. Ref of Material', size=64, required=False, ),
        'labour_sale_no': fields.char('Quote No. Ref of Labour', size=64, required=False, ),
        'project_name': fields.char('Product/Project Name', size=64, required=False,
            readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'mat_product_id': fields.many2one('product.product', 'Product of Material', readonly=True),
        'labour_product_id': fields.many2one('product.product', 'Product of Labour', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'type': fields.selection([
                            ('trading', 'Trading'),
                            ('project', 'Project'),
                            ('calibrate', 'Calibrate'),
                            ('repair', 'Repair'),
                            ('rent', 'Rent'),
                            ], 'Calc sheet Type', required=True, readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'overall_product_type': fields.selection([
                ('import', 'Imported'),
                ('domestic', 'Domestic'),
                ('mix', 'Mixed')], string='Overall Product Type', required=True, readonly=True),
        'note': fields.text('Terms and conditions'),
        'margins': fields.one2many('sale.profit.margin', 'prequote_id', 'Margins'),
        'import_tax': fields.function(_get_import_tax, digits_compute=dp.get_precision('Account'), string='import_taxImport Tax(%)',),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'currency_id': fields.many2one('res.currency', string="Currency", readonly=True, required=True,
                                       states={'draft': [('readonly', False)]}, track_visibility='always'),
        'cal_date': fields.date('Calculation Date', readonly=True, required=True,
                                states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='always'),
        'order_line': fields.one2many('sale.prequotation.product', 'pq_id', 'Calculation Area MATERIALS', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'order_line_labour': fields.one2many('sale.prequotation.labour', 'pq_id', 'Calculation Area LABOUR', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'doc_version': fields.integer('Version', required=True, readonly=True,),
        'pq_version': fields.integer('PQ Reversion', required=True, readonly=True,),
        'amount_material_cost': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Material Cost', track_visibility='always',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
            },
            multi='all'),
        'amount_labour_cost': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Labour Cost', track_visibility='always',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.labour': (_get_labour, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'amount_material_sale': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Materials', track_visibility='always',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
            },
            multi='all'),
        'amount_labour_sale': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Labour', track_visibility='always',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.labour': (_get_labour, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'percent_unforeseen': fields.float('Unforeseen (%)', digits_compute=dp.get_precision('Account'), readonly=True,
                                        states={'draft': [('readonly', False)]}, track_visibility='always',),
        'customer_commission': fields.float('Customer Commission', digits_compute=dp.get_precision('Account'), readonly=True,
                                        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='always'),
        'amount_unforeseen': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Unforeseen',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
                'percent_unforeseen': (lambda self, cr, uid, ids, c={}: ids, [], 20),
            },
            multi='all'),
        'amount_transport': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Transport',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
            },
            multi='all'),
        'amount_insurance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Insurance',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
            },
            multi='all'),
        'amount_import_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Import Tax',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
            },
            multi='all'),
        'amount_cost_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Grand Total Cost',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
                'sale.prequotation.labour': (_get_labour, [], 20),
            },
            multi='all'),
        'amount_sale_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Grand Total',
            store={
                'sale.prequotation': (lambda self, cr, uid, ids, c={}: ids, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
                'sale.prequotation.labour': (_get_labour, [], 20),
            },
            multi='all'),
        'acct_margin': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Accounting Margin',
            store={
                'sale.prequotation': (_get_pq, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
                'sale.prequotation.labour': (_get_labour, [], 20),
            },
            multi='all'),
        'acct_margin_percent': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Accounting Margin (%)',
            store={
                'sale.prequotation': (_get_pq, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
                'sale.prequotation.labour': (_get_labour, [], 20),
            },
            multi='all'),
        'margin': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Commission Margin',
            store={
                'sale.prequotation': (_get_pq, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
                'sale.prequotation.labour': (_get_labour, [], 20),
            },
            multi='all'),
        'margin_percent': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Commission Margin (%)',
            store={
                'sale.prequotation': (_get_pq, [], 20),
                'sale.prequotation.product': (_get_products, [], 20),
                'sale.prequotation.labour': (_get_labour, [], 20),
            },
            multi='all'),
        'convert_amount': fields.function(_get_convert_rate, digits_compute=dp.get_precision('Account'), string='Converted Amount', type='float',
            store={
                'sale.order': (_get_order_pq, ['state'], 10),
            }, multi='convert_rate', ),
        'convert_rate': fields.function(_get_convert_rate, string='Converted Rate', type='float', group_operator="avg",
            store={
                'sale.order': (_get_order_pq, ['state'], 10),
            }, multi='convert_rate',),
        'not_used': fields.boolean('Not Used'),
    }
    _defaults = {
        'not_used': False,
        'date_pq': fields.date.context_today,
        'cal_date': fields.date.context_today,
        'currency_id': _get_currency,
        'state': 'draft',
        'type': 'trading',
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.prequotation', context=c),
        'user_id': lambda obj, cr, uid, context: uid,
        'name': '/',
        'overall_product_type': 'domestic',
        'doc_version': 0,
        'pq_version': 1,
        'mat_sale_no': False,
        'labour_sale_no': False,
    }
    _order = 'name desc'

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return False
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        pricelist = part.property_product_pricelist or False
        if pricelist:
            return {'value': {'currency_id': pricelist.currency_id.id}}

    def on_change_caldate(self, cr, uid, ids, cal_date=False, context=None):
        if context is None:
            context = {}
        date = cal_date or time.strftime('%Y-%m-%d')
        margin_obj = self.pool.get('sale.margin.master')
        margin_ids = margin_obj.search(cr, uid, [], context=context)
        #Delete old margin
        preq_margin_obj = self.pool.get('sale.profit.margin')
        preqs = self.browse(cr, uid, ids, context)
        for preq in preqs:
            for margin in preq.margins:
                preq_margin_obj.unlink(cr, uid, [margin.id], context)
        margins_recs = []
        res = {'value': {}}

        ir_model_data = self.pool.get('ir.model.data')
        import_tax_id = ir_model_data.get_object(cr, uid, 'sale_prequotation', 'import_tax')

        for margin in margin_obj.browse(cr, uid, margin_ids, context=context):
            cr.execute("SELECT id,rate FROM margin_rate WHERE margin_id = %s AND name <= %s ORDER BY name desc LIMIT 1", (margin.id, date))
            rate = 0.0
            if cr.rowcount:
                rate_recs = cr.fetchall()
                rate = rate_recs[0][1]
                # Over write percentage of Import Tax in Product Lines
                if margin.id == import_tax_id.id:
                    for id in ids:
                        product_lines = self.pool.get('sale.prequotation.product').search(cr, uid, [('pq_id', '=', id)], context=context)
                        self.pool.get('sale.prequotation.product').write(cr, uid, product_lines, {'percentage': rate})
                    res['value'].update({'import_tax': rate})
            margins_recs.append({'margin_id': margin.id, 'name': margin.name, 'percentage': rate, })
        res['value'].update({'margins': margins_recs})
        return res

    #***********************************************************************
    #-----------------Common Method----------------------
    #***********************************************************************
    def _create_sale_lines(self, cr, uid, lines, sale_id, context=None):
        sale_line_obj = self.pool.get('sale.order.line')
        # kittiu: Getting tax_ids from sale_prequotation_tax_rule
        tax_rule_obj = self.pool.get('sale.prequotation.tax.rule')
        tax_ids = tax_rule_obj.get_matched_tax_ids(cr, uid, context.get('prequote_type', False),
                                context.get('split', False), context.get('quote_type', False), context)

        for line in lines:
            vals = {'order_id': sale_id,
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'tax_id': tax_ids and [(6, 0, tax_ids)] or \
                                [(6, 0, [x.id for x in line.product_id.taxes_id])],
                        'price_unit': line.price_unit_sale,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'state': 'draft',
                        }

            sale_line_obj.create(cr, uid, vals, context=context)
        return True

    def _get_default_sale_order(self, cr, uid, prequote, context=None):
        sale_obj = self.pool.get('sale.order')
        md = self.pool.get('ir.model.data')
        # Matching pricelist
        salepricelist = md.get_object_reference(cr, uid, 'product', 'pricelist_type_sale')[1]
        pricelist_type_obj = self.pool.get('product.pricelist.type')
        pricelist_type_name = pricelist_type_obj.browse(cr, uid, salepricelist, context=context).key

        pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [('currency_id', '=', prequote.currency_id.id), ('type', '=', pricelist_type_name), ('active', '=', True)], context=context)
        if not pricelist_ids:
            raise osv.except_osv(_('Warning!'), _('There is no Price List created for %s' % prequote.currency_id.name))
        pricelist = self.pool.get('product.pricelist').browse(cr, uid, pricelist_ids[0], context=context)

        sale_vals = sale_obj.onchange_partner_id(cr, uid, [], prequote.partner_id.id)
        sale_vals = sale_vals.get('value', {})
        sale_vals.update({'partner_id': prequote.partner_id.id,
                           'date_order': fields.date.context_today(self, cr, uid, context=context),
                           'state': 'draft',
                           'user_id': prequote.user_id.id,
                           'pq_id': prequote.id,
                           'overall_product_type': prequote.overall_product_type,
                           'doc_version': 1,
                           #'ref_attention_name': prequote.partner_contact_id,
                           'pricelist_id': pricelist.id})
        return sale_vals

    def versioning_sale_order(self, cr, uid, sale_id, context=None):
        if not context:
            context = {}
        if not context.get('version', False):
            return False
        else:
            #version = '-R-' + str(context.get('version', False))
            version = '-' + NUMBER_TO_CHAR[context.get('version', False)] or context.get('version', False)

        sale_obj = self.pool.get('sale.order')

        if sale_id:
            order = sale_obj.browse(cr, uid, sale_id, context=context)
            sale_obj.write(cr, uid, [sale_id], {'name': order.name + version, }, context=context)

        return True

    def _cancel_reference(self, cr, uid, prequote, context=None):
        sale_obj = self.pool.get('sale.order')
        sale_active = []
        order_name = {'mat_sale': {'id': False, 'doc_version': False, },
                      'labour_sale': {'id': False, 'doc_version': False, }}
        # Mat Line
        if prequote.mat_sale_id:
            sale_active.append(prequote.mat_sale_id.id)
            order_name.update({'mat_sale': {'id': prequote.mat_sale_id.id, 'doc_version': prequote.mat_sale_id.doc_version + 1, }})
            self.versioning_sale_order(cr, uid, prequote.mat_sale_id.id, context)

        if prequote.mat_sale_no:
            order_name['mat_sale'].update({'name': prequote.mat_sale_no})

        # Labour Line
        if prequote.labour_sale_id and prequote.labour_sale_id != prequote.mat_sale_id:
            sale_active.append(prequote.labour_sale_id.id)
            order_name.update({'labour_sale': {'id': prequote.labour_sale_id.id, 'doc_version': prequote.labour_sale_id.doc_version + 1, }})
            self.versioning_sale_order(cr, uid, prequote.labour_sale_id.id, context)

        if prequote.labour_sale_no:
            order_name['labour_sale'].update({'name': prequote.labour_sale_no})

        sale_obj.action_cancel(cr, uid, sale_active, context)

        # Update reference to Sale Order
        sale_order = {'mat_sale_id': None, 'labour_sale_id': None, 'mat_product_id': None, 'labour_product_id': None}
        self.write(cr, uid, [prequote.id], sale_order, context=context)
        return order_name

    #***********************************************************************
    #-----------------Create Quotation of List Type----------------------
    #***********************************************************************
    def _create_sale_order_type_list(self, cr, uid, prequote, amount_name, context_name, lines_name, order_field, order_no_name, context=None):
        if not context:
            context = {}
        sale_obj = self.pool.get('sale.order')
        # Create Sale Order
        sale_vals = self._get_default_sale_order(cr, uid, prequote, context)
        sale_vals.update({'amount_cost': prequote[amount_name],
                          'amount_transport': prequote.amount_transport,  # to_exclude
                          'amount_insurance': prequote.amount_insurance,  # to_exclude
                          'amount_import_tax': prequote.amount_import_tax})   # to_exclude
        sale = context.get(context_name, False)

        if sale:
            sale_vals.update(sale)

        quote = sale_obj.create(cr, uid, sale_vals, context=context)
        order = sale_obj.browse(cr, uid, quote, context)
        self._create_sale_lines(cr, uid, prequote[lines_name], quote, context)

        sale_order = {order_field: None, order_no_name: order.name}
        if prequote[lines_name]:
            sale_order.update({order_field: quote, })

        self.write(cr, uid, [prequote.id], sale_order, context=context)
        return quote

    def _sale_list_material(self, cr, uid, prequote, context=None):
        if not prequote.order_line:
            return False

        quote = self._create_sale_order_type_list(cr, uid, prequote, 'amount_cost_total', 'mat_sale', 'order_line', 'mat_sale_id', 'mat_sale_no', context)
        return quote

    def _sale_list_labour(self, cr, uid, prequote, context=None):
        if not prequote.order_line_labour:
            return False

        quote = self._create_sale_order_type_list(cr, uid, prequote, 'amount_labour_cost', 'labour_sale', 'order_line_labour', 'labour_sale_id', 'labour_sale_no', context)
        return quote

    def _sale_list(self, cr, uid, prequote, context=None):
        if not context:
            context = {}
        # Create Sale Order Lines
        quote = self._create_sale_order_type_list(cr, uid, prequote, 'amount_cost_total', 'mat_sale', 'order_line', 'mat_sale_id', 'mat_sale_no', context)
        # Form Labour
        self._create_sale_lines(cr, uid, prequote.order_line_labour, quote, context)

        sale_order = {'labour_sale_id': None}
        if prequote.order_line_labour:
            sale_order.update({'labour_sale_id': quote})
        self.write(cr, uid, [prequote.id], sale_order, context=context)
        return quote

    #***********************************************************************
    #-----------------Create Quotation of Bundle Type----------------------
    #***********************************************************************

    def _deactive_product(self, cr, uid, product_id, context=None):
        prod_obj = self.pool.get('product.product')
        prod_obj.write(cr, uid, [product_id], {'active': False}, context=context)
        return True

    def _get_category_project(self, cr, uid, context=None):
        md = self.pool.get('ir.model.data')
        res = False
        try:
            res = md.get_object_reference(cr, uid, 'sale_prequotation', 'product_category_project')[1]
        except ValueError:
            res = False
        return res

    def _create_product(self, cr, uid, product_name, context=None):
        prod_obj = self.pool.get('product.product')
        prod_name = product_name
        prod_val = prod_obj.default_get(cr, uid, ['uom_id', 'procure_method', 'supply_method', 'uom_po_id', 'categ_id', 'type', 'taxes_id', 'supplier_taxes_id', 'sale_ok', 'full_name'], context=context)
        prod_val.update({'name': prod_name})
        prod_val.update({'type': 'service'})
        prod_val.update({'sale_ok': False})
        prod_val.update({'purchase_ok': False})
        prod_val.update({'supply_method': 'bundle'})
        prod_val.update({'active': False})
        prod_val.update({'categ_id': self._get_category_project(cr, uid, context)})
        prod_val['taxes_id'] = [[6, False, prod_val['taxes_id']]]
        prod_val['supplier_taxes_id'] = [[6, False, prod_val['supplier_taxes_id']]]
        #Create new Product
        new_prod = prod_obj.create(cr, uid, prod_val, context=context)
        #Write full name
        prod_obj.write(cr, uid, [new_prod], {"name": prod_name}, context=context)
        return new_prod

    def _create_bundle(self, cr, uid, product_id, preqp_lines, context=None):
        prod_obj = self.pool.get('product.product')
        item_ids = []
        for line in preqp_lines:
            item_ids.append((0, 0, {'sequence': len(item_ids) + 1,
                             'item_id': line.product_id.id,
                             'uom_id': line.product_uom.id,
                             'qty_uom': line.product_uom_qty}))
        prod_obj.write(cr, uid, [product_id], {'item_ids': item_ids}, context=context)
        return True

    def _create_sale_order_type_project(self, cr, uid, product_id, prequote, amount_cost, sale_price, context_name, context=None):
        prod_obj = self.pool.get('product.product')
        sale_obj = self.pool.get('sale.order')
        sale_line_obj = self.pool.get('sale.order.line')
        prod_rec = prod_obj.browse(cr, uid, product_id, context=context)
        # kittiu: Getting tax_ids from sale_prequotation_tax_rule
        tax_rule_obj = self.pool.get('sale.prequotation.tax.rule')
        tax_ids = tax_rule_obj.get_matched_tax_ids(cr, uid, context.get('prequote_type', False),
                        context.get('split', False), context.get('quote_type', False), context)
        # Create Sale Order
        sale_vals = self._get_default_sale_order(cr, uid, prequote, context)
        sale_vals.update({'amount_cost': amount_cost,
                          'amount_transport': prequote.amount_transport,  # to_exclude
                          'amount_insurance': prequote.amount_insurance,  # to_exclude
                          'amount_import_tax': prequote.amount_import_tax})  # to_exclude
        sale = context.get(context_name, False)
        if sale:
            sale_vals.update(sale)
        quote = sale_obj.create(cr, uid, sale_vals, context=context)
        sale_line_obj.create(cr, uid, {'order_id': quote,
                                       'product_id': prod_rec.id,
                                       'product_uom_qty': 1,
                                       'price_unit': sale_price,
                                       'product_uom': prod_rec.uom_id.id,
                                       'state': 'draft',
                                       'tax_id': [(6, 0, tax_ids)] or \
                                                    [(6, 0, [x.id for x in prod_rec.taxes_id])],
                                       'name': prod_rec.name})
        order = sale_obj.browse(cr, uid, quote, context)
        return quote, order.name

    def _sale_project_material(self, cr, uid, prequote, context=None):
        if not prequote.order_line:
            return False
        prod_name = prequote.project_name + " (Material)"
        #Create Product
        new_prod = self._create_product(cr, uid, prod_name, context)
        #Create Sale Order
        quote, order_no = self._create_sale_order_type_project(cr, uid, new_prod, prequote, prequote.amount_material_cost,
                                                           prequote.amount_material_sale, 'mat_sale', context)
        #Create BOM
        loop_on = prequote.order_line
        self._create_bundle(cr, uid, new_prod, loop_on, context)
        #Update reference to Sale Order
        sale_order = {'mat_sale_id': None, 'mat_product_id': new_prod}
        if prequote.order_line:
            sale_order.update({'mat_sale_id': quote, 'mat_sale_no': order_no})

        self.write(cr, uid, [prequote.id], sale_order, context=context)

        return quote

    def _sale_project_labour(self, cr, uid, prequote, context=None):
        if not prequote.order_line_labour:
            return False
        #Create Product
        prod_name = prequote.project_name + " (Labour)"
        new_prod = self._create_product(cr, uid, prod_name, context)
        #Create Sale Order
        quote, order_no = self._create_sale_order_type_project(cr, uid, new_prod, prequote, prequote.amount_labour_cost,
                                                          prequote.amount_labour_sale, 'labour_sale', context)
        #Create Product Bundle
        loop_on = prequote.order_line_labour
        self._create_bundle(cr, uid, new_prod, loop_on, context)
        #Update reference to Sale Order
        sale_order = {'labour_sale_id': None, 'labour_product_id': new_prod}
        if prequote.order_line_labour:
            sale_order.update({'labour_sale_id': quote, 'labour_sale_no': order_no})
        self.write(cr, uid, [prequote.id], sale_order, context=context)
        return quote

    def _sale_project(self, cr, uid, prequote, context=None):
        #Create Product
        prod_name = prequote.project_name
        new_prod = self._create_product(cr, uid, prod_name, context)
        #Create Sale Order
        quote, order_no = self._create_sale_order_type_project(cr, uid, new_prod, prequote, prequote.amount_cost_total,
                                                           prequote.amount_sale_total, 'mat_sale', context)
        #Create Product Bundle
        loop_on = prequote.order_line + prequote.order_line_labour
        self._create_bundle(cr, uid, new_prod, loop_on, context)
        #Update reference to Sale Order
        sale_order = {'mat_sale_id': None, 'labour_sale_id': None, 'mat_product_id': new_prod, 'labour_product_id': new_prod}
        if prequote.order_line:
            sale_order.update({'mat_sale_id': quote, 'mat_sale_no': order_no})
        if prequote.order_line_labour:
            sale_order.update({'labour_sale_id': quote})
        self.write(cr, uid, [prequote.id], sale_order, context=context)

        return quote

    #***********************************************************************
    #-----------------Action----------------------
    #***********************************************************************
    def action_split_quotion(self, cr, uid, ids, format_quote, context=None):
        if context is None:
            context = {}

        quote_ids = []
        for prequote in self.browse(cr, uid, ids, context=context):

            if not (prequote.order_line_labour or prequote.order_line):
                continue

            ctx = context.copy()
            order_count = prequote.doc_version
            ctx.update({'version': order_count})
            old_order = self._cancel_reference(cr, uid, prequote, ctx)
            ctx.update(old_order)
            # kittiu: Add split / type into context
            ctx_mat = ctx.copy()
            ctx_lab = ctx.copy()
            ctx_mat.update({'split': True, 'prequote_type': prequote.type, 'quote_type': 'material', })
            ctx_lab.update({'split': True, 'prequote_type': prequote.type, 'quote_type': 'labour', })
            # --
            if format_quote == 'list':
                quote_ids.append(self._sale_list_material(cr, uid, prequote, ctx_mat))
                quote_ids.append(self._sale_list_labour(cr, uid, prequote, ctx_lab))
            else:
                quote_ids.append(self._sale_project_material(cr, uid, prequote, ctx_mat))
                quote_ids.append(self._sale_project_labour(cr, uid, prequote, ctx_lab))
            self.write(cr, uid, [prequote.id], {'split_flag': True, 'doc_version': order_count + 1, }, context)

        #Return is action view
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'sale_prequotation', 'action_prepq_quotation')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, quote_ids)) + "])]"
        return result

    def action_sale(self, cr, uid, ids, format_quote, context=None):
        if context is None:
            context = {}
        quote_ids = []
        for prequote in self.browse(cr, uid, ids, context=context):
            if not (prequote.order_line_labour or prequote.order_line):
                raise osv.except_osv(_('Warning!'), _("Please select Product(s)"))
            ctx = context.copy()
            order_count = prequote.doc_version
            ctx.update({'version': order_count})
            old_order = self._cancel_reference(cr, uid, prequote, ctx)
            ctx.update(old_order)

            # kittiu: Add split / type into context
            ctx_mat = ctx.copy()
            ctx_lab = ctx.copy()
            ctx_mat.update({'split': False, 'prequote_type': prequote.type, 'quote_type': 'material'})
            ctx_lab.update({'split': False, 'prequote_type': prequote.type, 'quote_type': 'labour'})
            # --

            if format_quote == 'list':
                quote_ids.append(self._sale_list(cr, uid, prequote, ctx_mat))
            else:
                quote_ids.append(self._sale_project(cr, uid, prequote, ctx_lab))

            self.write(cr, uid, [prequote.id], {'split_flag': False, 'doc_version': order_count + 1, }, context)

        #Return is action view
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'sale_prequotation', 'action_prepq_quotation')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, quote_ids)) + "])]"
        return result

    def action_new_pq_version(self, cr, uid, ids, context=None):
        for prequote in self.browse(cr, uid, ids, context=context):
            new_pq_id = self.copy(cr, uid, prequote.id, context=context)
            self.write(cr, uid, [new_pq_id], {
                'name': prequote.name + '-' + NUMBER_TO_CHAR[prequote.pq_version],
                'pq_id': prequote.id,
                'date_pq': prequote.date_pq,
                'cal_date': prequote.cal_date,
                'mat_sale_id': prequote.mat_sale_id.id,
                'labour_sale_id': prequote.labour_sale_id.id,
                'mat_sale_no': prequote.mat_sale_no,
                'labour_sale_no': prequote.labour_sale_no,
                'doc_version': prequote.doc_version,
                'state': 'cancel',
            }, context)
            self.write(cr, uid, [prequote.id], {
                'pq_version': prequote.pq_version + 1,
            }, context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.name:
                raise osv.except_osv(_('Error!'), 'Can not delete document with assigned number %s!' % (doc.name,))
        return super(sale_prequotation, self).unlink(cr, uid, ids, context=context)


class sale_prequotation_tax_rule(osv.osv):

    _name = 'sale.prequotation.tax.rule'
    _description = 'Calculation Sheet Tax Rule'
    _columns = {
        'prequote_type': fields.selection([
                            ('trading', 'Trading'),
                            ('project', 'Project'),
                            ('calibrate', 'Calibrate'),
                            ('repair', 'Repair'),
                            ('rent', 'Rent'),
                            ], 'Calc sheet Type', required=True),
        'split': fields.boolean('Split Material and Labour', required=False),
        'quote_type': fields.selection([
                ('material', 'Material'),
                ('labour', 'Labour')], string='Quotation Type'),
        'tax_ids': fields.many2many('account.tax', 'sale_prequotation_tax_rule_rel', 'rule_id', 'tax_id', 'Taxes', domain=['|', ('type_tax_use', '=', 'sale'), ('type_tax_use', '=', 'all')]),
    }
    _defaults = {
        'split': False,
    }
    _sql_constraints = [
        ('rule_uniq', 'unique(prequote_type, split, quote_type)', 'Selection combination must be unique!'),
    ]

    def get_matched_tax_ids(self, cr, uid, prequote_type, split, quote_type, context=None):
        res_ids = []
        tax_ids = []
        if not split:
            res_ids = self.search(cr, uid, [('prequote_type', '=', prequote_type), ('split', '=', False)])
        else:
            res_ids = self.search(cr, uid, [('prequote_type', '=', prequote_type), ('split', '=', True), ('quote_type', '=', quote_type)])
        if len(res_ids) > 1:
            raise osv.except_osv(_('Error!'), _("Matched more than 2 Calculation Sheet Tax Rule"))
        if len(res_ids) == 1:
            result = self.read(cr, uid, res_ids, ['tax_ids'])
            tax_ids = result[0]['tax_ids']
        return tax_ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
