# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 Gábor Dukai
#    Modified by Ecosoft Co., Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "TameTech Addons Installation",
    "version" : "1.0",
    "author" : "Ecosoft",
    "website" : "http://ecosoft.co.th",
    "description": """
Install all required modules
""",
    "depends" : [
                 # Standard Addons
                 'sale','purchase',
                 'stock','account',
                 'account_voucher',
                 'account_accountant',
                 'procurement',                
                 'base_import',
                 'base_report_designer',
                 'account_anglo_saxon',
                 'sale_prequotation',
                 
                 # Ecosoft and Revised Addons
                 'ac_report_font_thai',
                 'account_billing',
                 'product_uom_bycategory',
                 'product_flexible_search',
                 'invoice_address',
                 'doc_nodelete',
                 'picking_invoice_reltion',
                 'account_invoice_merge',
                 'invoice_cancel_ex',
                 'jasper_reports',
                 'payment_register',
                 'correct_deliver_bymistake',
                 
                 # TameTech Addons
                 'tt_config',
                 'jrxml_reports',
                 'hr',
                 ],
                 
    "auto_install": False,
    "application": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

