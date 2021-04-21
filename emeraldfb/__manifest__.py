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
    'version': '0.47',


    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'website',
        'hr',
        'stock',
        'purchase', 
        'hr_expense',
        # 'hr_holidays',
        # 'hr_payroll',
        # 'netcom_hr_payroll',
    ],

    # always loaded
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
        'views/website_sale_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
