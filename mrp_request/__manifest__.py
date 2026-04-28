{
    'name': "MRP REQUEST",

    'summary': "MRP Request for Manufacturing Module",

    'description': """
    New Feature for module MRP, MRP REQUEST
    """,

    'author': "Galang Krisna",
    'website': "https://youtu.be/dQw4w9WgXcQ?si=KoKTE880vsYW9bUb",

    'category': 'Supply Chain/Manufacturing',
    'version': '0.1',

    'depends': [
        'base',
        'mrp',
        'product',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/mrp_request_sequence.xml',
        'wizard/mrp_production_report_wizard.xml',
        'views/mrp_request_views.xml',
        'views/mrp_report_views.xml',
        'views/mrp_request_menus.xml',
        'reports/mrp_report_pdf_template.xml',
        'reports/mrp_report_pdf.xml',
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

