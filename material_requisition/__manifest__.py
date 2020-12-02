# -*- coding: utf-8 -*-
{
    'name': "Material Requisition",

    'summary': """
        Manage the request of materials internally from the Warehouse officers""",

    'description': """
        Manage the request of materials internally from the Warehouse officers
    """,

    'author': "MCEE Business Solutions",
    'website': "http://www.mceesolutions.com",

    'category': 'Stock',
    'version': '1.0.0',

    'depends': [
        'base',
        'hr',
        'product',
        'stock',
        'purchase',
        'purchase_requisition'
    ],

    'data': [
        'security/internal_requisition_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/sequence.xml',
        'views/hr_department.xml',
        'views/ir_request.xml',
        'views/res_company.xml',
        'views/purchase_requisition_view.xml',
        'wizards/ir_request.xml',
    ],
}
