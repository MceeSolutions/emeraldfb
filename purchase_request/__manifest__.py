# -*- coding: utf-8 -*-
{
    'name': "Purchase Request",

    'summary': """
        Purchase request module""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MCEE Business Solutions",
    'website': "http://www.mceebusinesssolutions.com",

    'category': 'Stock',
    'version': '0.1',

    'depends': ['base', 'stock', 'purchase', 'hr'],

    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/purchase_request_view.xml',
    ],
}