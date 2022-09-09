# -*- coding: utf-8 -*-
{
    'name': 'Account Invoice Customer Replacement (Mexican Localization)',

    'summary': """
    This module replace the customer on the PDF invoice document.""",

    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 34.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '15.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'l10n_mx_edi', 'cnd_l10n_mx_partner_edi_defaults'],

    # always loaded
    'data': [
        'views/res_config_setting.xml',
        'views/res_partner_views.xml',
        'views/report_invoice.xml',
        'views/report_payment.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
