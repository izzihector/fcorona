# -*- coding: utf-8 -*-
{
    'name': 'Partner Route and Supplier Category',

    'summary': """
    This module adds the partner route catalog and supplier category that are used to categorize partners and can be
    used in sale report and invoice report.""",

    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 25.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '15.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_route_views.xml',
        'views/supplier_category_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/account_invoice_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
