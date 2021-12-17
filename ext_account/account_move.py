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


class account_move(osv.osv):

    _inherit = 'account.move'

    def _get_year_date(self, cr, uid, ids, name, args, context=None):
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            res[move.id] = move.date and move.date.split('-')[0] or False
        return res

    _columns = {
        'year_date': fields.function(_get_year_date, type='char', string='Year',
            store={
                'account.move': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                }), 
    }

account_move()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
