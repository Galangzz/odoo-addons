# -*- coding: utf-8 -*-
{
    'name': "Purchase Approval",

    'summary': "Purchase Approval",

    'description': """
    Purchase Approval
    """,

    'author': "Galang Krisna P",
    'website': "https://github.com/Galangzz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'purchase'
    ],

    # always loaded
    'data': [
        'security/purchase_approval_security.xml',
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'application': True,
}

