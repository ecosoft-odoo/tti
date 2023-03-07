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

import time
import netsvc
from osv import osv, fields
from openerp.tools.translate import _


class commission_rule(osv.osv):
    _name = "commission.rule"
    _description = "Commission Rule"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'type': fields.selection((('percent_fixed', 'Fixed Percentage'),
                                  ('percent_amount', 'Percent By Amount'),
                                  ('percent_accumulate', 'Percent By Monthly Accumulated Amount')),
                                 'Type', required=True),
        'fix_percent': fields.float('Fix Percentage'),
        'rule_rates': fields.one2many('commission.rule.rate', 'commission_rule_id', 'Rates'),
        'rule_conditions': fields.one2many('commission.rule.condition', 'commission_rule_id', 'Conditions'),
        'active': fields.boolean('Active')
    }

    _defaults = {
        'active': True
    }

commission_rule()


class commission_rule_rate(osv.osv):

    _name = "commission.rule.rate"
    _description = "Commission Rule Rate"
    _columns = {
        'commission_rule_id': fields.many2one('commission.rule', 'Commission Rule'),
        'amount_over': fields.float('Amount Over', required=True),
        'amount_upto': fields.float('Amount Up-To', required=True),
        'percent_commission': fields.float('Commission (%)', required=True),
    }

    _order = 'id'

commission_rule_rate()


class commission_rule_condition(osv.osv):

    _name = "commission.rule.condition"
    _description = "Commission Rule Lines"
    _columns = {
        'sequence': fields.integer('Sequence', required=True),
        'commission_rule_id': fields.many2one('commission.rule', 'Commission Rule'),
        'sale_type': fields.selection((('domestic', 'Domestic'),
                                  ('import', 'Imported'),
                                  ('mix', 'Mixed')),
                                 'Sales Type', required=True),
        'sale_margin_over': fields.float('Margin Over (%)', required=True),
        'sale_margin_upto': fields.float('Margin Up-To (%)', required=True),
        'commission_coeff': fields.float('Commission Coeff', required=True),
        'accumulate_coeff': fields.float('Accumulate Coeff', required=True),
    }
    _defaults = {
        'commission_coeff': 1.0,
        'accumulate_coeff': 1.0
    }

    _order = 'sequence'

commission_rule_condition()


class sale_team(osv.osv):

    _name = "sale.team"
    _description = "Sales Team"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'commission_rule_id': fields.many2one('commission.rule', 'Commission Rule', required=True),
        'users': fields.many2many('res.users', 'sale_team_users_rel', 'tid', 'uid', 'Users'),
        'implied_ids': fields.many2many('sale.team', 'sale_team_implied_rel', 'tid', 'hid',
            string='Inherits', help='Users of this group automatically inherit those groups'),
        'skip_invoice': fields.boolean('Allow commission w/o invoice paid', help='Allow paying commission without invoice being paid. This is the case for trainees.')
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the team must be unique !')
    ]

sale_team()


class commission_worksheet(osv.osv):

    _name = 'commission.worksheet'
    _description = 'Commission Worksheet'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _search_wait_pay(self, cr, uid, obj, name, args, domain=None, context=None):
        if not len(args):
            return []
        lworksheet_obj = self.pool.get('commission.worksheet.line')

        for arg in args:
            if arg[1] == '=':
                if arg[2]:
                    lines = lworksheet_obj.search(cr, uid, [('invoice_paid', '=', 1), ('commission_paid', '=', 0)], context=context)
                else:
                    lines = lworksheet_obj.search(cr, uid, [('invoice_paid', '=', 1), ('commission_paid', '=', 1)], context=context)

        ids = self.search(cr, uid, [('worksheet_lines', 'in', lines), ('state', '=', 'confirmed')], context=context)

        return [('id', 'in', [id for id in ids])]

    def _invoice_wait_pay(self, cr, uid, ids, name, arg, context=None):
        lworksheet_obj = self.pool.get('commission.worksheet.line')
        res = {}.fromkeys(ids, {'wait_pay': False, })

        for id in ids:
            #Checking invoice was paid
            lines = lworksheet_obj.search(cr, uid, [('commission_worksheet_id', '=', id), ('state', '=', 'confirmed'), ('invoice_paid', '=', 1),
                                                   ('commission_paid', '=', 0)], context=context)
            if lines:
                res[id] = {'wait_pay': True, }
        return res

    def _get_period(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'sale_team_id': fields.many2one('sale.team', 'Team', required=True),
        'period_id': fields.many2one('account.period', 'Period', required=True,),
        'worksheet_lines': fields.one2many('commission.worksheet.line', 'commission_worksheet_id', 'Calculation Lines', ondelete='cascade'),
        'wait_pay': fields.function(_invoice_wait_pay, type='boolean', string='Invoice Paid', nct_search=_search_wait_pay, store=False),
        'state': fields.selection([('draft', 'Draft'),
                                   ('confirmed', 'Confirmed'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancelled')], 'Status', required=True, readonly=True,
                help='* The \'Draft\' status is set when the work sheet in draft status. \
                    \n* The \'Confirmed\' status is set when the work sheet is confirmed by related parties. \
                    \n* The \'Done\' status is set when the work sheet is ready to pay for commission. This state can not be undone. \
                    \n* The \'Cancelled\' status is set when a user cancel the work sheet.'),
    }

    _defaults = {
        'state': 'draft',
        'period_id': _get_period,
        'name': '/'
    }

    # _sql_constraints = [
    #     ('sale_team_id', 'period_id', 'Duplicate Sale Team / Period')
    # ]

    def create(self, cr, uid, vals, context=None):
        # if vals.get('period_id', False) and vals.get('sale_team_id', False):
        #     rec = self.search(cr, uid, [('period_id', '=', vals.get('period_id')), ('sale_team_id', '=', vals.get('sale_team_id'))], context=context)
        #     if rec:
        #         raise osv.except_osv(_('Warning!'),
        #                          _('You can not create duplicate Commission WorkSheet'))
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'commission.worksheet') or '/'
        return super(commission_worksheet, self).create(cr, uid, vals, context=context)

    def _get_match_rule_condition(self, cr, uid, rule, order, context=None):
        if context is None:
            context = {}
        rule_condition_obj = self.pool.get('commission.rule.condition')
        rule_condition_ids = rule_condition_obj.search(cr, uid, [('commission_rule_id', '=', rule.id), # Rule
                                                ('sale_type', '=', order.overall_product_type), # Sale Type
                                                ('sale_margin_over', '<', order.percent_margin), # % Margin
                                                ('sale_margin_upto', '>=', order.percent_margin)
                                                ])
        if not rule_condition_ids:
            return False
        elif len(rule_condition_ids) > 1:
            raise osv.except_osv(_('Error!'), 
                                _('More than 1 Rule Condition match %s! There seems to be problem with Rule %s.') % (order.name, rule.name))
        elif len(rule_condition_ids) == 1:
            return rule_condition_ids[0]

    def _calculate_commission(self, cr, uid, rule, amount_to_accumulate, accumulated_amt, context=None):
        if context is None:
            context = {}
        commission_amt = 0.0
        amount_from = accumulated_amt - amount_to_accumulate
        ranges = rule.rule_rates
        for range in ranges:
            commission_rate = range.percent_commission / 100
            # Case 1: In Range, get commission and quit.
            if amount_from <= range.amount_upto and accumulated_amt <= range.amount_upto:
                commission_amt += amount_to_accumulate * commission_rate
                break
            # Case 2: Over Range, only get commission for this range first and postpone to next range.
            elif amount_from <= range.amount_upto and accumulated_amt > range.amount_upto:
                range_amount = (range.amount_upto - amount_from)
                commission_amt += range_amount * commission_rate
                amount_to_accumulate -= range_amount
                amount_from = range.amount_upto
        return commission_amt

    def action_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'})
        return True

    def _get_product_commission(self, cr, uid):
        ir_model_data = self.pool.get('ir.model.data')
        product = ir_model_data.get_object(cr, uid, 'commission_calc', 'product_product_commission')
        return product.id

    def action_create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        context.update({'type': 'in_invoice'})
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        inv_obj = self.pool.get('account.invoice')
        invline_obj = self.pool.get('account.invoice.line')
        sale_order_team = self.pool.get('sale.team')

        invoice_ids = []

        worksheets = self.browse(cr, uid, ids, context=context)
        product_id = self._get_product_commission(cr, uid)
        for worksheet in  worksheets:
            #Get line not paid commission
            teams = sale_order_team.browse(cr, uid, [worksheet.sale_team_id.id], context=context)
            if teams and teams[0] and teams[0].skip_invoice:
                line_ids = worksheet_line_obj.search(cr, uid, [('commission_worksheet_id', '=', worksheet.id), ('commission_paid', '=', False)])
            else:
                line_ids = worksheet_line_obj.search(cr, uid, [('commission_worksheet_id', '=', worksheet.id), ('commission_paid', '=', False), ('invoice_paid', '=', True)])
            if not line_ids:
                raise osv.except_osv(_('Warning!'), _("No Commission Invoice(s) can be created for Worksheet %s" % (worksheet.name)))

            #Create invoice for each sale person in team
            for user in worksheet.sale_team_id.users:

                #******Create invoice********
                #initial value of invoice
                inv_rec = inv_obj.default_get(cr, uid,
                                              ['type', 'state', 'journal_id', 'currency_id', 'company_id', 'reference_type', 'check_total',
                                               'internal_number', 'user_id', 'sent'], context=context)

                inv_rec.update(inv_obj.onchange_partner_id(cr, uid, [], 'in_invoice', user.partner_id.id, company_id=inv_rec['company_id'])['value'])
                inv_rec.update({'origin': worksheet.name, 'type': 'in_invoice', 'partner_id': user.partner_id.id, 'date_invoice': time.strftime('%Y-%m-%d'), })

                invoice_id = inv_obj.create(cr, uid, inv_rec, context=context)
                invoice_ids.append(invoice_id)

                wlines = worksheet_line_obj.browse(cr, uid, line_ids, context=context)
                for wline in wlines:
#                   #initial value of invoice lines
                    inv_line_rec = (invline_obj.product_id_change(cr, uid, [], product_id, False, 1, name=False, type='in_invoice', partner_id=user.partner_id.id, fposition_id=False,
                                                                   price_unit=0, currency_id=inv_rec['currency_id'], context=None, company_id=inv_rec['company_id'])['value'])
                    inv_line_rec.update({
                                         'name': 'Commission in period ' + worksheet.period_id.name,
                                         'origin': wline.order_id.name,
                                         'invoice_id': invoice_id,
                                         'product_id': product_id,
                                         'partner_id': user.partner_id.id,
                                         'company_id': inv_rec['company_id'],
                                         'currency_id': inv_rec['currency_id'],
                                         'price_unit': wline.commission_amt,
                                         'price_subtotal': wline.commission_amt,
                                         })

                    invline_obj.create(cr, uid, inv_line_rec, context=context)
                    #Update worksheet line was paid commission
                    worksheet_line_obj.write(cr, uid, [wline.id], {'commission_paid': True}, context)

                if worksheet_line_obj.search_count(cr, uid, [('commission_worksheet_id', '=', worksheet.id), ('commission_paid', '=', False)]) <= 0:
                    #All worksheet lines has been paid will update state of worksheet is done.
                    self.write(cr, uid, [worksheet.id], {'state': 'done'})

        #Show new Invoice
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree2')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, invoice_ids)) + "])]"
        result['name'] = 'Commission invoice(s)'
        return result

    def action_calculate(self, cr, uid, ids, context=None):

        if context is None:
            context = {}

        period_obj = self.pool.get('account.period')
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        order_obj = self.pool.get('sale.order')
        rule_condition_obj = self.pool.get('commission.rule.condition')
        cur_obj = self.pool.get('res.currency')

        for worksheet in self.browse(cr, uid, ids):
            sale_team_id = worksheet.sale_team_id.id
            period_id = worksheet.period_id.id
            if not sale_team_id or not period_id:
                continue

            rule = worksheet.sale_team_id.commission_rule_id
            date_start = period_obj.browse(cr, uid, period_id).date_start
            date_stop = period_obj.browse(cr, uid, period_id).date_stop
            # Delete old lines
            line_ids = worksheet_line_obj.search(cr, uid, [('commission_worksheet_id', '=', worksheet.id)])
            worksheet_line_obj.unlink(cr, uid, line_ids)

            # Search for matched Completed Sales Order
            cr.execute("select o.id from sale_order o \
                                join sale_order_team t on o.id = t.sale_id \
                                where o.state in ('progress','manual','done') \
                                and date_order >= %s and date_order <= %s \
                                and t.sale_team_id = %s and (o.not_used is null or o.not_used = false) order by o.id", (date_start, date_stop, sale_team_id))
            order_ids = map(lambda x: x[0], cr.fetchall())

            # Remove duplicate 'order_ids' from other commission worksheet in the same team and period
            match_worksheet_line_ids = worksheet_line_obj.search(cr, uid,
                [('commission_worksheet_id.sale_team_id', '=', worksheet.sale_team_id.id), ('commission_worksheet_id.period_id', '=', worksheet.period_id.id), ('commission_worksheet_id', '!=', worksheet.id)])
            match_worksheet_lines = worksheet_line_obj.browse(cr, uid, match_worksheet_line_ids)
            match_order_ids = [mwl.order_id.id for mwl in match_worksheet_lines]
            order_ids = [order_id for order_id in order_ids if order_id not in match_order_ids]

            # Create lines from Order
            orders = order_obj.browse(cr, uid, order_ids)
            accumulated_amt = 0.0
            for order in orders:
                # For each order, find its match rule line
                amount_to_accumulate = 0.0
                commission_amt = 0.0
                rule_condition_id = self._get_match_rule_condition(cr, uid, rule, order, context=context)

                # Get amount by currency
                amount_currency = 0.0
                company_currency = self.pool['res.company'].browse(cr, uid, order.company_id.id).currency_id.id
                ctx = context.copy()  
                ctx.update({'date': order.date_order})
                ctx.update({'pricelist_type': 'sale'})
                if order.currency_id.id <> company_currency:
                    amount_currency = cur_obj.compute(cr, uid, order.currency_id.id, company_currency, order.amount_net, context=ctx)
                else:
                    amount_currency = order.amount_net
                # --
                if rule_condition_id:
                    rule_condition = rule_condition_obj.browse(cr, uid, rule_condition_id)
                    amount_to_accumulate = amount_currency * rule_condition.accumulate_coeff
                    accumulated_amt += amount_to_accumulate
                    # accumulated_amt += order.amount_net
                    commission_amt = self._calculate_commission(cr, uid, rule, amount_to_accumulate, accumulated_amt, context=context)
                    commission_amt = commission_amt * rule_condition.commission_coeff
                res = {
                    'commission_worksheet_id': worksheet.id,
                    'order_id': order.id,
                    'sale_type': order.overall_product_type,
                    'order_date': order.date_order,
                    'order_amt': amount_currency,
                    'margin': order.pq_margin,
                    'percent_margin': order.percent_margin,
                    'accumulated_amt': accumulated_amt,
                    'commission_amt': commission_amt,
                }
                worksheet_line_obj.create(cr, uid, res)

        return True

commission_worksheet()


class commission_worksheet_line(osv.osv):

    _name = "commission.worksheet.line"
    _description = "Commission Worksheet Lines"

    def _search_invoice_done(self, cr, uid, obj, name, args, domain=None, context=None):
        if not len(args):
            return []
        # Only allow checking invoice_paid = 'true'
        assert len(args) == 1 and args[0][1] in ('=') and args[0][2], 'expression is not what we expect: %r' % args
        
        sale_obj = self.pool.get('sale.order')
        order_ids = sale_obj.search(cr, uid, [('invoiced', args[0][1], args[0][2])])
        # It seem to be bug even in OpenERP. function and search function of 'invoiced' do not return the same result. Need to double check.
        for sale in sale_obj.browse(cr, uid, order_ids, context=context):
            if not sale.invoiced:
                order_ids.remove(sale.id)
        return [('order_id', 'in', order_ids)]
        
    def _is_invoice_done(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, {'invoice_paid': False, })
        data_objs = self.browse(cr, uid, ids, context=context)
        for data in data_objs:
            res[data.id] = {'invoice_paid': data.order_id.invoiced, }
        return res

    _columns = {
        'commission_worksheet_id': fields.many2one('commission.worksheet', 'Commission Worksheet'),
        'order_id': fields.many2one('sale.order', 'Order Number'),
        'order_date': fields.date('Order Date'),
        'order_amt': fields.float('Order Amount', readonly=True),
        'sale_type': fields.selection((('domestic', 'Domestic'),
                                  ('import', 'Imported'),
                                  ('mix', 'Mixed')),
                                 'Sales Type', required=True),
        'margin': fields.float('Margin', readonly=True),
        'percent_margin': fields.float('% Margin', readonly=True),
        'accumulated_amt': fields.float('Accumulated Amount', readonly=True),
        'commission_amt': fields.float('Commission Amount', readonly=True),
        'invoice_paid': fields.function(_is_invoice_done, type='boolean', string='Invoice Paid',
                                        fnct_search=_search_invoice_done, multi="invoice", store=False),
        'commission_paid': fields.boolean('Commission Created', readonly=True),
    }

    _order = 'id'

    def unlink(self, cr, uid, ids, context=None):
        line_ids = self.search(cr, uid, [('id', 'in', ids), ('commission_paid', '=', 1)], context=context)
        if line_ids and len(line_ids) > 0:
            wlines = self.browse(cr, uid, line_ids)
            order_ids = [wline.order_id.name for wline in wlines]
            raise osv.except_osv(_('Error!'), _("You can't delete this Commission Worksheet, because commission has been issued for Sales Order No. %s"%(",".join(order_ids))))  
        else:
            return super(commission_worksheet_line, self).unlink(cr, uid, ids, context=context)

commission_worksheet_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
