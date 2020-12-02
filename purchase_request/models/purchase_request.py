# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api

class purchase_request(models.Model):
    _name = 'purchase_request.purchase_request'

    name = fields.Char("Description")
    number = fields.Char(string="Number", default="/")
    date = fields.Date("Request Date", default=datetime.now())
    request_by = fields.Many2one("res.partner", "Requested By", default=lambda self: self.env.user.partner_id.id)
    description = fields.Text("Additional Comments")
    state = fields.Selection([
        ('draft', "New"), 
        ('open', "Confirmed"), 
        ('validate', "Validated"),
        ('approve', "Approved")], string="State", readony=True, default="draft")

    def get_requester_department(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        department_id = employee_id and employee_id.department_id.id
        return department_id

    department_id = fields.Many2one("hr.department", string="Department", default=get_requester_department)
    request_line = fields.One2many(
        string='Request Line',
        comodel_name='purchase_request.purchase_request_line',
        inverse_name='request_id',
    )
    purchase_document = fields.Char("Created PO")
    
    def submit_request(self):
        self.state = "open"

    def validate_request(self):
        self.state = "validate"

    def approve_request(self):
        self.number = self.env['ir.sequence'].next_by_code('purchase_request.purchase_request')
        purchase_order = self.env['purchase.order'].create({
            'date_order': datetime.now(),
            'partner_id': 23,
            'currency_id': self.env.user.company_id.currency_id.id,
            'company_id': self.env.user.company_id.id,
            'picking_type_id': 2,
            'origin': self.number,
            'order_line': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'date_planned': datetime.now(),
                'product_uom': line.product_id.uom_id.id,
                'price_unit': line.product_id.standard_price,
            }) for line in self.request_line]
        })
        self.purchase_document = purchase_order.name
        self.state = "approve"


class PurchaseRequestLine(models.Model):
    _name = "purchase_request.purchase_request_line"
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        ondelete='restrict',
    )
    quantity = fields.Float(string="Quantity")
    comment = fields.Char(string="Comment")
    request_id = fields.Many2one(comodel_name="purchase_request.purchase_request", string="Request")
    