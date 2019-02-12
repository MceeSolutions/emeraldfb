# -*- coding: utf-8 -*-
import datetime

from datetime import date, timedelta
from odoo import models, fields, api

from odoo.addons import decimal_precision as dp

class Picking(models.Model):
    _name = "stock.picking"
    _inherit = 'stock.picking'
    
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        return self.env['hr.employee'].search([('user_id','=',self.env.uid)])

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        readonly=False, required=True,
        states={'draft': [('readonly', False)]})
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    
    employee_id = fields.Many2one('hr.employee', 'Employee',
            states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_employee,
            help="Default Owner")

    @api.multi
    def manager_confirm(self):
        for order in self:
            order.write({'man_confirm': True})
        return True
    
    def _default_owner(self):
        return self.env.context.get('default_employee_id') or self.env['res.users'].browse(self.env.uid).partner_id
    
    owner_id = fields.Many2one('res.partner', 'Owner',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_owner,
        help="Default Owner")
    
    man_confirm = fields.Boolean('Manager Confirmation', track_visibility='onchange')
    net_lot_id = fields.Many2one(string="Serial Number", related="move_line_ids.lot_id", readonly=True)
    internal_transfer = fields.Boolean('Internal Transfer?', track_visibility='onchange')
    
    @api.multi
    def button_reset(self):
        self.mapped('move_lines')._action_cancel()
        self.write({'state': 'draft'})
        return {}
    
    '''
    @api.model
    def create(self, vals):
        a = super(Picking, self).create(vals)
        a.send_store_request_mail()
        return a
        return super(Picking, self).create(vals)
    
    
    @api.multi
    def send_store_request_mail(self):
        if self.state in ['draft','waiting','confirmed']:
            group_id = self.env['ir.model.data'].xmlid_to_object('stock.group_stock_manager')
            user_ids = []
            partner_ids = []
            for user in group_id.users:
                user_ids.append(user.id)
                partner_ids.append(user.partner_id.id)
            self.message_subscribe_users(user_ids=user_ids)
            subject = "A new store request {} has been made".format(self.name)
            self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
            return False
        return True
    
    @api.multi
    def send_store_request_done_mail(self):
        if self.state in ['done']:
            subject = "Store request {} has been approved and validated".format(self.name)
            partner_ids = []
            for partner in self.sheet_id.message_partner_ids:
                partner_ids.append(partner.id)
            self.sheet_id.message_post(subject=subject,body=subject,partner_ids=partner_ids)
    '''
            
class HrExpense(models.Model):

    _name = "hr.expense"
    _inherit = 'hr.expense'
    
    vendor_id = fields.Many2one('res.partner', string="Vendor", domain=[('supplier', '=', True)], readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})
    
    @api.multi
    def approve_employee_expense_sheets_notification(self):
        group_id = self.env['ir.model.data'].xmlid_to_object('emeraldfb.group_coo')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe_users(user_ids=user_ids)
        subject = "Expense {} needs a COO Approval".format(self.name)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
    
    @api.multi
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': [line.id for line in self],
                'default_employee_id': self[0].employee_id.id,
                'default_name': self[0].name if len(self.ids) == 1 else '',
                'default_vendor_id' :  self[0].vendor_id.id if self[0].vendor_id else ''
            }
        }        
            
    
class HrExpenseSheet(models.Model):
    _name = "hr.expense.sheet"
    _inherit = 'hr.expense.sheet'
    
    state = fields.Selection([('submit', 'Submitted'),
                              ('confirm', 'Confirmed'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='submit', required=True,
    help='Expense Report State')
    
    @api.multi
    def approve_employee_expense_sheets(self):
        self.write({'state': 'confirm'})
        group_id = self.env['ir.model.data'].xmlid_to_object('emeraldfb.group_coo')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe_users(user_ids=user_ids)
        subject = "Expense {} needs COO Approval".format(self.name)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
    
    @api.multi
    def refuse_employee_expense_sheets(self):
        self.write({'state': 'cancel'})
    
    @api.multi
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr.group_hr_manager'):
            raise UserError(_("Only HR Managers can approve expenses"))
        
        self.write({'state': 'approve', 'responsible_id': self.env.user.id})
        
        
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    state_id = fields.Many2one(comodel_name="res.country.state", string='State', ondelete='restrict', readonly=True, index=True, store=True, related='partner_id.state_id')
    city = fields.Char(string='City', readonly=True, index=True, store=True, related='partner_id.city')

class SaleReport(models.Model):
    _name = "sale.report"
    _inherit = "sale.report"
    
    state_id = fields.Many2one(comodel_name="res.country.state", string='State', ondelete='restrict', readonly=True, index=True, store=True, related='partner_id.state_id')
    city = fields.Char(string='City', readonly=True, index=True, store=True, related='partner_id.city')
    
    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
                    sum(l.amt_to_invoice / COALESCE(cr.rate, 1.0)) as amt_to_invoice,
                    sum(l.amt_invoiced / COALESCE(cr.rate, 1.0)) as amt_invoiced,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.confirmation_date as confirmation_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.state_id as state_id,
                    s.city as city,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.analytic_account_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str
    
    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.name,
                    s.date_order,
                    s.confirmation_date,
                    s.partner_id,
                    s.state_id,
                    s.city,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    s.analytic_account_id,
                    s.team_id,
                    p.product_tmpl_id,
                    partner.country_id,
                    partner.commercial_partner_id
        """
        return group_by_str
    
    
class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ['purchase.order.line']
    
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    
    @api.depends('product_qty', 'discount', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            