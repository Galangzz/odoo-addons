{
    'name': "Currency Fetch",

    'summary': "Currency Fetch",

    'description': """
    Ulululululul
    """,

    'author': "Galang Krisna P",
    'website': "",

    'category': 'Unauthorized',
    'version': '0.1',

    'depends': ['base', 'account'],

    'data': [
        'views/currency_fetch_view.xml',
    ],
    
    'installable': True,
    'application': True,
        'assets': {
        'web.assets_backend': [
            'web/static/src/xml/**/*',
        ],
    },
    'license': 'AGPL-3',
}

