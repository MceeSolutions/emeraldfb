from odoo import models, fields


class account_payment(models.Model):
    _name = "account.payment"
    _inherit = "account.payment"    
    
    user_id = fields.Many2one('res.users','User', readonly=True, track_visibility='onchange', default=lambda self: self.env.uid)
