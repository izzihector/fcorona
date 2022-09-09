# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
# -*- coding: utf-8 -*-
{
    'name': 'Factura Global POS (Mexico SAT)',

    'summary': """
    Con este módulo puedes generar una Factura Global de pedidos de Punto de Venta de sesiones abiertas o cerradas.""",

    'description': """
    Factura Global de pedidos de Punto de Venta que cumple con los requisitos del SAT o factura genérica para cualquier cliente.""",

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 132.00,
    'maintainer': 'José Candelas',
    # 'live_test_url': 'https://www.youtube.com/watch?v=vWjKCwlyMdE',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '15.0.1.5',

    # Changelog
    # 14.0.1.4: price_subtotal > 0.00 to be included on the global invoice
    # 14.0.1.5: line.price_subtotal < 0.00 and invoice_type == 'out_refund'

    # TODO 2021:
    # 1. Colocar un campo para indicar que es factura global, en factura y en Nota de crédito
    # 2. Agregar ese campo en el Análisis de Facturas
    # 3. Tener la opción de crear o no la Nota de crédito

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'uom',
        'point_of_sale',
        'account',
        'cnd_l10n_mx_partner_edi_defaults_invoice',
    ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'views/res_config_setting.xml',
        'views/pos_payment_method_views.xml',
        'views/account_move_views.xml',
        'views/product_template_views.xml',
        'views/l10n_mx_edi_cfdiv33.xml',
        'wizard/wizard_pos_invoice.xml',
        'data/global_invoice_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
# https://exdoo.mx/factura-global-de-punto-de-venta-con-odoo/
