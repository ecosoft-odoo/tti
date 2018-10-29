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

from openerp.osv import osv


class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        res = super(account_voucher, self).recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
        rec_count = len(res['value']['line_cr_ids'])
        i = 0
        # In case due date in line greater than current due date ,it will delete.
        while i < rec_count:
            record = res['value']['line_cr_ids'][i]
            if (not record.get('date_due', False)) or record['date_due'] > date:
                del res['value']['line_cr_ids'][i]
                rec_count = len(res['value']['line_cr_ids'])
            else:
                i += 1

        rec_count = len(res['value']['line_dr_ids'])
        i = 0
        # In case due date in line greater than current due date ,it will delete.
        while i < rec_count:
            record = res['value']['line_dr_ids'][i]
            if (not record.get('date_due', False)) or record['date_due'] > date:
                del res['value']['line_dr_ids'][i]
                rec_count = len(res['value']['line_dr_ids'])
            else:
                i += 1
        return res

account_voucher()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
