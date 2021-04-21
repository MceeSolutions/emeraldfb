from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    payment_term_id = fields.Many2one(comodel_name = 'account.payment.term', string ='Payment Terms')
    
    client_birthday = fields.Date(string= 'Client Birthday Date')
    
   