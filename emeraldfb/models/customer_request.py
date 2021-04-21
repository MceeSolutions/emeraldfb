from odoo import models, fields, api


class CustomerRequest(models.Model):
    
    _name = "customer.request"
    _description = "customer request form"
    _order = "name"
    _inherit = ['res.partner']
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')          
    
    payment_term_id = fields.Many2one(comodel_name = 'account.payment.term', string ='Payment Terms')
    
    @api.depends('is_company', 'parent_id.commercial_partner_id')
    def _compute_commercial_partner(self):
        return {}
         
    @api.multi
    def button_reset(self):
        self.write({'state': 'draft'})
        return {}
    
    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})
        return {}
    
    @api.multi
    def button_approve(self):
        self.write({'state': 'approve'})
        vals = {
            'name' : self.name,
            'company_type' : self.company_type,
            'image' : self.image,
            'parent_id' : self.parent_id.id,
            'street' : self.street,
            'street2' : self.street2,
            'city' : self.city,
            'state_id' : self.state_id.id,
            'zip' : self.zip,
            'country_id' : self.country_id.id,            
            'vat' : self.vat,
            'function' : self.function,
            'phone' : self.phone,
            'mobile' : self.mobile,
            'email' : self.email,
            'customer': self.customer,
            'user_id': self.user_id.id,
            'property_product_pricelist': self.property_product_pricelist.id,
            'payment_term_id': self.payment_term_id.id,
            'supplier' : self.supplier,
            'supplier' : self.company_id.id
        }
        self.env['res.partner'].sudo().create(vals)
        return {}
    
    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        return {}

