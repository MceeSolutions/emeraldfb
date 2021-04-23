from datetime import date
from odoo import models, fields


class VendorQualification(models.Model):
    _name = 'vendor.qualification'
    _description = 'Vendor Qualification'

    name = fields.Char(string="Potential Vendor Name")
    email = fields.Char(string="Email")
    website = fields.Char(string="Website")
    reg_number = fields.Char(string="Registration Number")
    phone = fields.Char(string="Phone")
    street = fields.Char(string="Street")
    city = fields.Char(string="City")
    contact_name = fields.Char(string="Contact Person")
    contact_phone = fields.Char(string="Contact Phone")
    contact_email = fields.Char(string="Contact Email")
    category = fields.Char(string="Category")
    state = fields.Selection(selection=[
        ('draft', 'New'),
        ('submit', 'Validate'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], default="draft", help="""
    When a request is created, state is draft, 
    when the creator confirms that all is fine, it moves to submit
    After reviewing the document provided by the vendor, the project manager approves it
    """)
    partner_id = fields.Many2one(comodel_name='res.partner', string="Vendor")
    date_submitted = fields.Date(string="Submitted on", readonly=True)
    submitted_by = fields.Many2one(comodel_name="res.users", string="Submitted by", readonly=True)
    approved_by = fields.Many2one(comodel_name="res.users", string="Approved By", readonly=True)
    date_approved = fields.Date(string="Approved on", readonly=True)
    vendor_count = fields.Integer(string="Vendors", compute="get_vendors")

    def get_vendors(self):
        self.vendor_count = len(self.partner_id)

    def action_view_vendor(self):
        action = self.env.ref('account.res_partner_action_supplier')
        result = action.read()[0]
        result['context'] = {'search_default_supplier': 1,'res_partner_search_mode': 'supplier', 'default_is_company': True, 'default_supplier_rank': 1}
        res = self.env.ref('base.view_partner_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.partner_id.id
        return result

    def submit(self):
        self.submitted_by = self.env.uid
        self.date_submitted = date.today()        
        self.state = 'submit'

    def approve(self):
        vendor = self.env['res.partner'].create({
            'name': self.name,
            'supplier_rank': 1,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'street': self.street,
            'city': self.city,
            'child_ids': [(0, 0, {
                'name': self.contact_name,
                'phone': self.contact_phone,
                'email': self.contact_email,
            })],
        })
        self.approved_by = self.env.uid
        self.date_approved = date.today()
        self.partner_id = vendor.id
        self.state = 'approve'

    def reject(self):
        self.state = 'reject'

    def re_open(self):
        self.state = 'draft'