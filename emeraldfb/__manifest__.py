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

    'category': 'emeraldfb',
    'version': '0.48',

    'depends': [
        'base',
        'sale',
        'hr',
        'stock',
        'purchase', 
        'hr_expense',
    ],
    
    'data': [
        'security/emeraldfb_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
        'views/payment_view.xml',
        'views/training_view.xml',
        'views/purchase_view.xml',
        'views/recruitment_view.xml',
        'views/customer_request_view.xml',
    ],
}
