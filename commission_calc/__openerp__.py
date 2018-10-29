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
    'name' : "Commission Calculation for TameTech",
    'author' : 'Ecosoft',
    'summary': '',
    'description': """
Commission Management.
====================================
    * Sale Teams
    * Commission rules
    * Commission Work Sheet
    
Key Features
------------
    * Manage Sale Teams
    * Manage Commission Rules
    * Create Commission Work Sheet from Sale Order by Month
    * Create Supplier Invoice from Commission Work Sheet  
""",
    'category': 'Sales',
    'sequence': 8,
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['sale','account','sale_prequotation','currency_rate_enhanced'],
    'demo' : [
        'commission_calc_demo.xml'],
    'data' : [
        'commission_calc_data.xml',
        'commission_calc_view.xml',
        'sale_order_view.xml',
        'commission_product_data.xml',
        'commission_calc_sequence.xml'
    ],
    'test' : [
        '/test/commission_calc_demo.yml'
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
