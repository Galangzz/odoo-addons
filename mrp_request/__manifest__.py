{
    'name': "MRP REQUEST",

    'summary': "MRP Request for Manufacturing Module",

    'description': """
    New Feature for module MRP, MRP REQUEST
    """,

    'author': "Galang Krisna",
    'website': "https://www.yourcompany.com",

    'category': 'Supply Chain/Manufacturing',
    'version': '19.0.1.0.0',

    'depends': [
        'base',
        'mrp',
        'product',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/mrp_request_sequence.xml',
        'views/mrp_request_views.xml',
        'views/mrp_report_views.xml',
        'views/mrp_request_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
    'assets': {
        'web.assets_backend': [
            'mrp_request/static/src/js/kanban_controller_patch.js',
        ],
    },
}

