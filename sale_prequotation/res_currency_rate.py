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
from openerp.osv import osv, fields


class res_currency(osv.osv):

    _inherit = "res.currency"

    def _current_rate_calc(self, cr, uid, ids, name, arg, context=None):
        return self._current_rate_computation_calc(cr, uid, ids, name, arg, True, context=context)

    def _current_rate_silent_calc(self, cr, uid, ids, name, arg, context=None):
        return self._current_rate_computation_calc(cr, uid, ids, name, arg, False, context=context)

    def _current_rate_computation_calc(self, cr, uid, ids, name, arg, raise_on_no_rate, context=None):
        if context is None:
            context = {}
        res = {}
        if 'date' in context:
            date = context['date']
        else:
            date = time.strftime('%Y-%m-%d')
        date = date or time.strftime('%Y-%m-%d')
        # Convert False values to None ...
        currency_rate_type = context.get('currency_rate_type_id') or None
        # ... and use 'is NULL' instead of '= some-id'.
        operator = '=' if currency_rate_type else 'is'
        for id in ids:
            cr.execute("SELECT currency_id, calc_sheet_rate FROM res_currency_rate WHERE currency_id = %s AND name <= %s AND currency_rate_type_id " + operator + " %s ORDER BY name desc LIMIT 1", (id, date, currency_rate_type))
            if cr.rowcount:
                id, rate = cr.fetchall()[0]
                res[id] = rate
            elif not raise_on_no_rate:
                res[id] = 0
            else:
                raise osv.except_osv(_('Error!'), _("No currency rate associated for currency %d for the given period" % (id)))
        return res

    _columns = {
        'calc_sheet_rate': fields.function(_current_rate_calc, string='Calc Sheet Rate', digits=(12, 6),
            help='The rate for compute in Calc Sheet'),
         # Do not use for computation ! Same as rate field with silent failing
        'calc_rate_silent': fields.function(_current_rate_silent_calc, string='Current Rate', digits=(12, 6),
            help='The rate of the currency to the currency of rate 1 (0 if no rate defined).'),
     }

    def _get_conversion_rate_calc(self, cr, uid, from_currency, to_currency, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'currency_rate_type_id': ctx.get('currency_rate_type_from')})
        from_currency = self.browse(cr, uid, from_currency.id, context=ctx)

        ctx.update({'currency_rate_type_id': ctx.get('currency_rate_type_to')})
        to_currency = self.browse(cr, uid, to_currency.id, context=ctx)

        if from_currency.calc_sheet_rate == 0 or to_currency.calc_sheet_rate == 0:
            date = context.get('date', time.strftime('%Y-%m-%d'))
            if from_currency.calc_sheet_rate == 0:
                currency_symbol = from_currency.symbol
            else:
                currency_symbol = to_currency.symbol
            raise osv.except_osv(_('Error'), _('No rate found \n' \
                    'for the currency: %s \n' \
                    'at the date: %s') % (currency_symbol, date))
        # kittiu: check Smaller/Bigger currency
        to_rate = to_currency.type_ref_base == 'bigger' and (1 / to_currency.calc_sheet_rate) or to_currency.calc_sheet_rate
        from_rate = from_currency.type_ref_base == 'bigger' and (1 / from_currency.calc_sheet_rate) or from_currency.calc_sheet_rate
        # --
        return to_rate / from_rate

    def compute_rate_calc(self, cr, uid, from_currency_id, to_currency_id, from_amount,
                round=True, currency_rate_type_from=False, currency_rate_type_to=False, context=None):
        if not context:
            context = {}
        if not from_currency_id:
            from_currency_id = to_currency_id
        if not to_currency_id:
            to_currency_id = from_currency_id
        xc = self.browse(cr, uid, [from_currency_id, to_currency_id], context=context)
        from_currency = (xc[0].id == from_currency_id and xc[0]) or xc[1]
        to_currency = (xc[0].id == to_currency_id and xc[0]) or xc[1]
        if (to_currency_id == from_currency_id) and (currency_rate_type_from == currency_rate_type_to):
            if round:
                return self.round(cr, uid, to_currency, from_amount)
            else:
                return from_amount
        else:
            context.update({'currency_rate_type_from': currency_rate_type_from, 'currency_rate_type_to': currency_rate_type_to})
            rate = self._get_conversion_rate_calc(cr, uid, from_currency, to_currency, context=context)
            if round:
                return self.round(cr, uid, to_currency, from_amount * rate)
            else:
                return from_amount * rate


class res_currency_rate(osv.osv):
    _inherit = "res.currency.rate"

    _columns = {
        'calc_sheet_rate': fields.float('Calc Sheet Rate', digits=(12, 6), help='The rate for compute in Calc Sheet'),
     }

res_currency_rate()
