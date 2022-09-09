# -*- coding: utf-8 -*-
{
    "name": "Importar XML a facturas (Localización Mexicana)",

    'summary': """
    Importación de facturas de clientes y de proveedores desde archivos XML y PDF (opcional).""",

    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 199.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],
    'category': 'Accounting',
    'version': '15.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'l10n_mx_edi', 'sale'],

    # always loaded
    'data': [
        'data/account_tax_data.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'wizard/upload_edi_invoices.xml',
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
# TODO: 1. Agragar campo en el proveedor "Cuenta de importación de XML": account.accout dominio: deprecated=false
#         user_type_id=15
#         Cuando importas facturas regulares de proveedor, cada vez que se importe una factura so toma esa cuenta
#         para cada línea de factura de ese proveedor
#       2. Preparar para 4.0
#       3. Importar pagos desde xml
