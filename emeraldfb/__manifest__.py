# -*- coding: utf-8 -*-
{
    'name': "Emeraldfb",

    'summary': """
        Emeraldfb Modules""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MCEE Solutions",
    'website': "http://www.mceesolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'emeraldfb',
    'version': '0.31',


    # any module necessary for this one to work correctly
    'depends': ['base','sale','website','hr','stock','purchase', ],

    # always loaded
    'data': [
        'security/emeraldfb_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/stock_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
