# -*- coding: utf-8 -*-
{
    'name': "Label Picking - Zebra Printer",

    'summary': """
        Impresión de etiquetas Zebra para pickings""",

    'description': """
        Módulo para imprimir etiquetas con formato ZPL para impresoras Zebra
        específicamente para operaciones de picking de stock.
    """,

    'author': "Jaime León",
    'website': "empaquetadurasyempaques.com",
    'license': 'LGPL-3',
    'icon': '/static/src/description/icon.png',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Inventory',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'wizard/zebra_label_wizard_views.xml',
        'report/zebra_label_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
