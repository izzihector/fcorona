# -*- coding: utf-8 -*-
{
    'name': 'Factura Compacta (Localización Mexicana)',

    'summary': """
        Modifica la plantilla de factura para que el PDF sea más compacta y agrega campos de la localización mexicana.
    """,

    'description': """
         1. Compacta las líneas de factura para mostrar más en cada página.
         2. Al facturar a un contacto de un cliente, eliminar el nombre del contacto para dejar solamente el nombre de la empresa.
         3. Agrega los campos "Divisa" y el "Tipo de cambio" en caso de que la factura sea en una moneda extranjera.
         4. Agrega los campos "RFC", "Dirección Fiscal", "Régimen Fiscal" y "Lugar de Expedición" del emisor.
         5. Agrega los campos "Folio Fiscal" (UUID) y "CFDI Origen" en el encabezado de la factura
         6. Agrega la columna "Partida" en la líneas de factura.
         7. Separa la columna "Descripción" en dos columnas, "Código" y "Descripción" (del producto).
         8. Cambia la etiqueta "Referencia" por "Orden de Compra" del cliente.
         9. Reemplaza el encabezado y pie de página de los reportes por unos más compactos.
        10. Modifica los valores de márgenes y espacio del encabezado en el formato tamaño carta (US Letter) y coloca este fomato como defecto del formato de informes.
        11. Modifica la dirección "Salida para informes" y "Formato de la calle" para el país México para incluir campos de la localización mexicana.
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 49.00,
    'maintainer': 'José Candelas',
    # 'live_test_url': 'https://www.youtube.com/watch?v=vWjKCwlyMdE',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '15.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'l10n_mx_edi'],

    # always loaded
    'data': [
        'views/report_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
}
