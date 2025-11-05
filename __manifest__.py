# -*- coding: utf-8 -*-
{
    'name': "Delivery Expenses - Payment Receipt Portal",

    'summary': """
        Portal management system for supplier payment receipt processing.
        Allows portal users to upload evidence and complete delivery tasks.
    """,

    'description': """
        ## Payment Receipt Portal Module

        Specialized module for managing supplier payment receipts in a portal environment.

        **Key Features:**
        - Assign payment receipt tasks to portal users
        - Portal interface for uploading evidence documents
        - Automated file validation and security
        - Workflow audit trail and notifications
        - Multi-company support

        **Main Models:**
        - delivery_expenses.payment_task: Portal tasks assigned to users
        - delivery_expenses.payment_receipt_file: Evidence files uploaded by portal users

        **Dependencies:**
        - stock: For supplier.payment.receipt model
        - mail: For chatter and notifications
        - portal: For portal user support
    """,

    'author': "Jaime león",
    'website': "https://www.empaquetadurasyempaques.com",

    'category': 'receipt',
    'version': '15.0.1.0.0',
    'icon': '/delivery_expenses/static/src/description/icon.png',

    'depends': [
        'base',
        'stock',
        'mail',
        'portal',
        'supplier_payment_receipts',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/payment_task_views.xml',
        'views/supplier_payment_receipt_views.xml',
        'wizard/assign_task_wizard_views.xml',
        'views/portal_menu.xml',
        'views/portal_templates.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'auto_install': False,
}
