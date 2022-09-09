# -*- coding: utf-8 -*-
{
    'name': "Restringir timbrar facturas y pagos (Localización Mexicana)",

    'summary': """
        Localización Mexicana - CFDI 3.3
        Este módulo es para decidir si se va a timbrar o no una factura, por defecto se van a timbrar las facturas.
        Es posible definir clientes que por defecto no se timbren sus facturas.
    """,

    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 99.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '15.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'sale', 'product', 'sale_stock', 'account', 'l10n_mx_edi'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'data/ir_actions_server_data.xml',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/report_invoice.xml',
        'report/account_invoice_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
