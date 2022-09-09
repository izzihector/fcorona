# -*- coding: utf-8 -*-
{
    'name': 'Multiple Zip Code Ranges for Shipping Methods',

    'summary': """
    Define multiple multiple Zip code ranges in Shipping Methods.
    """,

    'description': """
    With this module is posible to define in "Shipping Methods" multiple Zip code ranges instead just one.
    It is also possible to define e-commerce exclusive "Shipping Methods",
    this is useful to limit the customer to see more "Shipping Methods" if there is an exclusive one that matches
    the address rules, which can be one with additional charge, for example.
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 39.00,
    'maintainer': 'José Candelas',
    # 'live_test_url': 'https://www.youtube.com/watch?v=vWjKCwlyMdE',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'eCommerce',
    'version': '15.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['delivery', 'website_sale', 'website_sale_delivery'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_carrier.xml',
        'views/delivery_carrier_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
