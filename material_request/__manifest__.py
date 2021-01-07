# -*- coding: utf-8 -*-
{
    'name': "Material Request",

    'summary': """
        Request for Material""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MCEE Business Solutionsy",
    'website': "http://www.mceesolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'stock'],

    'data': [
        # 'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/material_request.xml',
    ],
}