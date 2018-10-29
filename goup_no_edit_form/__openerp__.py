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

{
    'name': "New user group w/o form edit",
    'author': 'Ecosoft',
    'summary': '',
    'description': """

This module will create a new group 'No Edit Form INV/DO' (group_no_edit_form)

Add this group to any user, user will not see Edit button in following form,

* Customer Invoice
* Delivery Order

""",
    'category': 'Base',
    'sequence': 8,
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['account', 'stock'],
    'demo': [],
    'data': [
            'security/group.xml',
            'no_edit_form_view.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
